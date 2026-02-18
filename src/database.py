
import os
import json
import shutil
import pygame
import sqlite3
import numpy as np
import pandas as pd
import configparser
from time import time
from tqdm import tqdm
from pathlib import Path
from copy import deepcopy
from unidecode import unidecode
from scipy.spatial.distance import cdist

# Object to manage the buttons
from buttons import (Button_selection, Button_app_actions, Text, Inidication,
                     Button_keyboard)

pygame.init()

class DataGest:
    """
    Parent class managing the logic: 
        - Manipulation of SQLite Zotero/Better-BibTeX databases.
        - Data processing via Pandas and NumPy.
        - Management of the application state and buttons.

    """

    # To resize the window, modify this SCALE factor
    SCALE = 1.1

    # Frame Per Seconds
    FPS = 60

    # Colors
    bg_color = (245, 245, 213)  # Cream background
    bt_color = (180, 180, 180)  # Grey for buttons/panels

    def __init__(self):
        # Window size
        self.WIDTH  = 1200 * self.SCALE
        self.HEIGHT =  700 * self.SCALE

        # font to use
        self.TEXT_FONT  = pygame.font.SysFont(
            'Arial', max([1, int(20*self.SCALE)]))

        self.TITLE_FONT = pygame.font.SysFont(
            'Arial', max([1, int(30*self.SCALE)]), bold=True)

        # --- G/UI Constants ---
        self.mx_tx_y     =  23        # Max number of lines visible in
        #                               comparison panel
        self.text_height =  30 *self.SCALE # Vertical space for each line of
        #                                    text
        self.TXT_LEN = [380*self.SCALE, 385*self.SCALE] # text lenght limits
        self.COMP_LINES  = [785*self.SCALE, 790*self.SCALE,
                            800*self.SCALE] # comparison pannel limits
        self.COMP_TX_X   = [405*self.SCALE, 795*self.SCALE] # x comparison 
        #                                                     text position
        self.COMP_TX_DY  = 5*self.SCALE # y offset comparison text
        # Comparison feilds x midle line division
        self.DIVIDERS = 790*self.SCALE

        # white empty box
        self.box_tx = [400*self.SCALE, 0, 800*self.SCALE, self.HEIGHT]

        # Current Y position of the scrollbar thumb
        self.fscroll = [1180*self.SCALE, 0, 20*self.SCALE, self.HEIGHT]
        self.bscroll = [1181*self.SCALE, max([1, 3 * self.SCALE]),
                          18*self.SCALE, 692 * self.SCALE]

        # --- Gestion de l'État ---
        self.state = 'IDLE'  # IDLE, LOADING, COMPUTING, ERROR, etc.
        self.error_type = '' # For the error type gestion
        self.comp_st = 0     # Compilation state (0: empty, 1: loaded,
        #                       2: compiled)

        # --- Paths and files ---
        self.from_path = '' # origin path of the databse
        self.to_path = ''   # path where to copy the database

        # --- Data structur ---
        self.data = {}          # raw Zotero tables
        self.data_cite_key = {} # Better-BibTeX citation keys
        self.one_loaded = False # True if db has been successfully loaded

        self.papers = {}      # Indexed by Citation Key
        self.authors = {}     # Indexed par first and last name
        self.num_elem = 0     # Total number of documents

        # --- Comparison parameters (with buttons interactions) ---
        self.to_compare = None # 'lastname', 'firstname' or 'bothname'
        self.to_filter = None  # 'today', 'tod-1w', etc.
        self.treshold = 0.10   # treshold value for distance based algorithm

        self.use_special = np.array([False]) # Keep or not the accents
        self.filter_abv = np.array([False])  # Use only or not abreviations
        self.add_key = np.array([False])     # Render citation keys
        self.both_comp = 'AND' # how both name distance will be handle

        self.auth_len_last  = np.zeros(0) # if last  name isn't given
        self.auth_len_first = np.zeros(0) # if first name isn't given
        self.letters   = {'l':{}, 'f':{}} # founded letter with bag column
        self.bag_last  = np.zeros(0)      # last  name per letter count
        self.bag_first = np.zeros(0)      # first name per letter count

        # copy of papers
        self.papers_save = {}
        # optimization for comparison
        self.auth_abv = np.zeros(0)

        # --- Time gestion (NumPy vectorised) ---
        self.today = np.array([time()]).astype('datetime64[s]').astype(
            'datetime64[D]')

        self.tod_1w = self.today -   7 # today minus one week
        self.tod_1m = self.today -  31 # today minus one month
        self.tod_1y = self.today - 365 # today minus one year
        self.auth_time = np.zeros(0)   # for optimised comparison

        # --- Comparison results ---
        self.liste1 = [] # 1st list of the last / first name comparison
        self.liste2 = [] # 2nd list of the last / first name comparison
        self.light  = [] # if the line is white or grey

        # --- Buttons initialisation ---
        # Tab selection buttons
        self.pannels_bt = Button_selection(
            x_start=np.array([  0, 100, 250]) * self.SCALE,
            x_stop =np.array([100, 250, 400]) * self.SCALE,
            y_start=np.array([  0,   0,   0]) * self.SCALE,
            y_stop =np.array([ 50,  50,  50]) * self.SCALE,
            text=np.array(['Data', 'Settings', 'Execution']),
            font=self.TITLE_FONT, lin_w=3, target='pannel',
            values=np.array(['DATA', 'SETTINGS', 'EXECUTION']),
            empty_sel=None, colors=[self.bg_color, self.bg_color])

        # Buttons list for the Data pannel
        self.data_buttons = [
            # Database loading button
            Button_app_actions(
            x_start=np.array([ 25]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([ 60]) * self.SCALE,
            y_stop =np.array([100]) * self.SCALE,
            text=np.array(['(Re)Load database']),
            font=self.TEXT_FONT, lin_w=3,
            target='load_db_manager', bt_color=self.bt_color),

            # Database compile button
            Button_app_actions(
            x_start=np.array([ 25]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([110]) * self.SCALE,
            y_stop =np.array([150]) * self.SCALE,
            text=np.array(['Compile the database']),
            font=self.TEXT_FONT, lin_w=3,
            target='compile_database', bt_color=self.bt_color),

            # Algorithms buttons
            Button_selection(
            x_start=np.array([100, 100, 100]) * self.SCALE,
            x_stop =np.array([300, 300, 300]) * self.SCALE,
            y_start=np.array([180, 230, 280]) * self.SCALE,
            y_stop =np.array([220, 270, 320]) * self.SCALE,
            text=np.array(['Perfect', 'Levenshtein', 'Damerau-Levenshtein',
                           ]),
            font=self.TEXT_FONT, lin_w=3, target='algo',
            values=np.array(['Perfect', 'Levenshtein', 'DamerauLevenshtein'
                             ]),
            empty_sel=None, colors=[(20, 250, 75), self.bt_color])]

        # Buttons list for the Matching algorithm
        self.matching_bt = [
            # How the authors will be compared buttons
            Button_selection(
            x_start=np.array([ 45, 245]) * self.SCALE,
            x_stop =np.array([155, 355]) * self.SCALE,
            y_start=np.array([100, 100]) * self.SCALE,
            y_stop =np.array([140, 140]) * self.SCALE,
            text=np.array(['Last name', 'First name']),
            font=self.TEXT_FONT, lin_w=3, target='to_compare',
            values=np.array(['lastname', 'firstname']),
            empty_sel=None, colors=[(20, 250, 75), self.bt_color]),

            # If the "special" letters are used or not (é -> e) button
            Button_selection(
            x_start=np.array([240]) * self.SCALE,
            x_stop =np.array([360]) * self.SCALE,
            y_start=np.array([200]) * self.SCALE,
            y_stop =np.array([240]) * self.SCALE,
            text=np.array(['Special']), font=self.TEXT_FONT, lin_w=3,
            target='use_special', values=np.array([True]),
            empty_sel=np.array([False]), colors=[(20, 250, 75), (255, 0, 0)]),

            # If the abbreviation are used to filter button
            Button_selection(
            x_start=np.array([ 40]) * self.SCALE,
            x_stop =np.array([160]) * self.SCALE,
            y_start=np.array([200]) * self.SCALE,
            y_stop =np.array([240]) * self.SCALE,
            text=np.array(['Abreviation']), font=self.TEXT_FONT, lin_w=3,
            target='filter_abv', values=np.array([True]),
            empty_sel=np.array([False]),
            colors=[(20, 250, 75), self.bt_color])]

        # Buttons list for the Levenshtein algorithm
        self.levenshtein_bt = [
            # How the authors will be compared buttons
            Button_selection(
            x_start=np.array([  5, 145, 285]) * self.SCALE,
            x_stop =np.array([115, 255, 395]) * self.SCALE,
            y_start=np.array([100, 100, 100]) * self.SCALE,
            y_stop =np.array([140, 140, 140]) * self.SCALE,
            text=np.array(['Last name', 'First name', 'Both name']),
            font=self.TEXT_FONT, lin_w=3, target='to_compare',
            values=np.array(['lastname', 'firstname', 'bothname']),
            empty_sel=None, colors=[(20, 250, 75), self.bt_color]),

            # If the "special" letters are used or not (é -> e) button
            Button_selection(
            x_start=np.array([140]) * self.SCALE,
            x_stop =np.array([260]) * self.SCALE,
            y_start=np.array([200]) * self.SCALE,
            y_stop =np.array([240]) * self.SCALE,
            text=np.array(['Special']), font=self.TEXT_FONT, lin_w=3,
            target='use_special', values=np.array([True]),
            empty_sel=np.array([False]), colors=[(20, 250, 75), (255, 0, 0)]),

            # Define the treshold distance under which strings can be the same
            Button_keyboard(
            x_start=np.array([160]) * self.SCALE,
            x_stop =np.array([360]) * self.SCALE,
            y_start=np.array([300]) * self.SCALE,
            y_stop =np.array([340]) * self.SCALE,
            text='0.10', font=self.TEXT_FONT, lin_w=2,
            target='treshold', bounds=[0., 1.]),
        
            # How the comparison is done when both name is selected
            Button_selection(
            x_start=np.array([  5, 145, 285]) * self.SCALE,
            x_stop =np.array([115, 255, 395]) * self.SCALE,
            y_start=np.array([400, 400, 400]) * self.SCALE,
            y_stop =np.array([440, 440, 440]) * self.SCALE,
            text=np.array(['AND', 'OR', 'Average']),
            font=self.TEXT_FONT, lin_w=3, target='both_comp',
            values=np.array(['AND', 'OR', 'AVG']),
            empty_sel=np.array([True, False, False]),
            colors=[(20, 250, 75), (255, 0, 0)])]

        # Buttons list for the Demarau-Levenshtein algorithm
        self.D_levenshtein_bt = [
            # How the authors will be compared buttons
            Button_selection(
            x_start=np.array([  5, 145, 285]) * self.SCALE,
            x_stop =np.array([115, 255, 395]) * self.SCALE,
            y_start=np.array([100, 100, 100]) * self.SCALE,
            y_stop =np.array([140, 140, 140]) * self.SCALE,
            text=np.array(['Last name', 'First name', 'Both name']),
            font=self.TEXT_FONT, lin_w=3, target='to_compare',
            values=np.array(['lastname', 'firstname', 'bothname']),
            empty_sel=None, colors=[(20, 250, 75), self.bt_color]),

            # If the "special" letters are used or not (é -> e) button
            Button_selection(
            x_start=np.array([140]) * self.SCALE,
            x_stop =np.array([260]) * self.SCALE,
            y_start=np.array([200]) * self.SCALE,
            y_stop =np.array([240]) * self.SCALE,
            text=np.array(['Special']), font=self.TEXT_FONT, lin_w=3,
            target='use_special', values=np.array([True]),
            empty_sel=np.array([False]), colors=[(20, 250, 75), (255, 0, 0)]),

            # Define the treshold distance under which strings can be the same
            Button_keyboard(
            x_start=np.array([160]) * self.SCALE,
            x_stop =np.array([360]) * self.SCALE,
            y_start=np.array([300]) * self.SCALE,
            y_stop =np.array([340]) * self.SCALE,
            text='0.10', font=self.TEXT_FONT, lin_w=2,
            target='treshold', bounds=[0., 1.]),
        
            # How the comparison is done when both name is selected
            Button_selection(
            x_start=np.array([  5, 145, 285]) * self.SCALE,
            x_stop =np.array([115, 255, 395]) * self.SCALE,
            y_start=np.array([400, 400, 400]) * self.SCALE,
            y_stop =np.array([440, 440, 440]) * self.SCALE,
            text=np.array(['AND', 'OR', 'Average']),
            font=self.TEXT_FONT, lin_w=3, target='both_comp',
            values=np.array(['AND', 'OR', 'AVG']),
            empty_sel=np.array([True, False, False]),
            colors=[(20, 250, 75), (255, 0, 0)])]

        # Buttons list for execution tab
        self.execution_bt = [
            # Filter on the date of the documents addition buttons
            Button_selection(
            x_start=np.array([ 40, 240,  40, 240]) * self.SCALE,
            x_stop =np.array([160, 360, 160, 360]) * self.SCALE,
            y_start=np.array([100, 100, 150, 150]) * self.SCALE,
            y_stop =np.array([140, 140, 190, 190]) * self.SCALE,
            text=np.array(['Today', '-1 week', '-1 month', '-1 year']),
            font=self.TEXT_FONT, lin_w=3, target='to_filter',
            values=np.array(['today', 'tod-1w', 'tod-1m', 'tod-1y']),
            empty_sel=None, colors=[(20, 250, 75), self.bt_color]),

            # If Better bibtex citation keys are displayed button
            Button_selection(
            x_start=np.array([ 75]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([260]) * self.SCALE,
            y_stop =np.array([300]) * self.SCALE,
            text=np.array(['Display the citation key']),
            font=self.TEXT_FONT, lin_w=3, target='add_key',
            values=np.array([True]), empty_sel=np.array([False]),
            colors=[(20, 250, 75), self.bt_color]),

            # Compare first/last name of the authors button
            Button_app_actions(
            x_start=np.array([ 75]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([470]) * self.SCALE,
            y_stop =np.array([510]) * self.SCALE,
            text=np.array(['Show']), font=self.TEXT_FONT, lin_w=3,
            target='compute_show', bt_color=self.bt_color),

            # To reset parameters button
            Button_app_actions(
            x_start=np.array([ 75]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([520]) * self.SCALE,
            y_stop =np.array([560]) * self.SCALE,
            text=np.array(['Reset']), font=self.TEXT_FONT,
            lin_w=3, target='reinit', bt_color=self.bt_color),

            # To export the comparison between authors button
            Button_app_actions(
            x_start=np.array([ 75]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([570]) * self.SCALE,
            y_stop =np.array([610]) * self.SCALE,
            text=np.array(['Export comparaison']),
            font=self.TEXT_FONT, lin_w=3,
            target='compute_export_show', bt_color=self.bt_color),

            # To export the database into a json file button
            Button_app_actions(
            x_start=np.array([ 75]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([630]) * self.SCALE,
            y_stop =np.array([670]) * self.SCALE,
            text=np.array(['Export db as json']),
            font=self.TEXT_FONT, lin_w=3,
            target='export_jsonf', bt_color=self.bt_color)]

        # Which tab to show
        self.pannel = 'DATA' # DATA, SETTINGS, EXECUTION

        # Wich algorithm is choose
        self.algo = None # Perfect, Levenshtein, DamerauLevenshtein

        # Text fields
        self.matching_txt = Text([200*self.SCALE]*3, np.array([75, 120, 170]
            )*self.SCALE, ['Compare by:', '/', 'Filters:'], self.TITLE_FONT)

        self.levenshtein_txt = Text(np.array([200, 130, 270, 200, 150, 185,
            130, 270])*self.SCALE, np.array([75, 120, 120, 180, 280, 380, 420,
            420])*self.SCALE, ['To use:', '/', '/', 'Transform:',
            'Maximum distance:', 'Reduction for both name:', '/', '/'],
            self.TITLE_FONT)

        self.dam_lev_txt = Text(np.array([200, 130, 270, 200, 150, 185, 130,
            270])*self.SCALE, np.array([75, 120, 120, 180, 280, 380, 420, 420]
            )*self.SCALE, ['To use:', '/', '/', 'Transform:',
            'Maximum distance:', 'Reduction for both name:', '/', '/'],
            self.TITLE_FONT)

        self.execution_txt = Text(np.array([200]*3)*self.SCALE,
            np.array([75, 120, 170])*self.SCALE, ['Filters:', '/', '/'],
            self.TITLE_FONT)

        # Loading state square
        self.load_sq = Inidication([342.5*self.SCALE, 60*self.SCALE,
                                    40*self.SCALE, 40*self.SCALE], [200,0,0])
        # Compilation state square
        self.comp_sq = Inidication([342.5*self.SCALE, 110*self.SCALE,
                                    40*self.SCALE, 40*self.SCALE], [200,0,0])

        # --- Warning messages dictionaries ---
        self.waiting_messages = {
            'LOADING': 'Databases are being loaded...',
            'COMPUTING': 'Database is being compiled...',
            'COMPARING': 'Authors comparaison is being computed...',
            'EXPORTING': 'Database is being exported...'}

        # --- Error messages dictionaries ---
        y_centers = (np.array([350, 400, 450, 500]) * self.SCALE).tolist()
        self.error_messages = {
         'no file':{'text':[
           'No database was found from the given access path, make',
            'sure you writte the correct path in the "main.ini" file.',
            'Given path:', str(self.from_path)],
          'y_center':y_centers},

         'no betbib':{'text':[
           'No Better-BibTex database was found from the given access path,',
           'make sure you writte the correct path in the "main.ini" file.',
           'Given path:', str(self.from_path)],
          'y_center':y_centers},

         'no database':{'text':[
           "No database has yet been imported, merged into one with:",
           "'(Re)Load database' before trying to compile."],
          'y_center':y_centers[:2]},

         'no compil': {'text':[
           "The loaded database has not yet been compiled. Compile it with:",
           "'Compile the database' before trying to use it."],
          'y_center':y_centers[:2]},

         'no compar':{'text':[
           "You need to choose how the authors will compare using the ",
           "buttons: 'Last name' / 'First name'."],
          'y_center':y_centers[:2]},

         'len0':{'text':["Maximum distance fields is empty !"],
         'y_center':y_centers[:1]},

         'nan':{'text':[
          "Maximum distance is not a number !",
          "Maximum distance field have multiple '.',",
          "only one can be present."],
         'y_center':y_centers[:3]},

         'st.':{'text':[
          "Maximum distance is not a number !",
          "Maximum distance field have multiple '.',",
          "only one can be present."],
         'y_center':y_centers[:3]},

         '0n':{'text':[
          "Maximum distance is not a number !",
          "Maximum distance field have multiple '.',",
          "only one can be present."],
         'y_center':y_centers[:3]},

         'over':{'text':[
          "Maximum distance is too high !",
          "Maximum distance must be lower or equal to 1."],
         'y_center':y_centers[:2]},

         'under':{'text':[
          "Maximum distance is too low !",
          "Maximum distance must be greater or equal to 0."],
         'y_center':y_centers[:2]}}

    def reduce_string(self, string:str) -> str:
        """
        Function to remove space and dot in a string

        Parameters
        ----------
        string : str
            String to clean.

        Returns
        -------
        str
            Cleaned string.

        """
        return string.replace(' ', '').replace('.', '')

    def duplicate_table(self) -> None:
        """
        Function to duplicate the database tagerted with the main.ini file to
        be able to read sql file even when Zotero app is running.
        """
        config = configparser.ConfigParser()
        config.read('main.ini')
        self.from_path = Path(config['PATH'].get('DATA_PATH'))
        self.to_path = Path(config['PATH'].get('SAVE_PATH'))
        self.to_path.mkdir(parents=True, exist_ok=True)
        if os.path.isfile(self.from_path / 'zotero.sqlite'):
            shutil.copyfile(self.from_path / 'zotero.sqlite',
                            self.to_path   / 'zotero.sqlite')

            if os.path.isfile(self.from_path / 'better-bibtex.sqlite'):
                shutil.copyfile(self.from_path / 'better-bibtex.sqlite',
                                self.to_path   / 'better-bibtex.sqlite')


            elif os.path.isfile(self.from_path / 'better-bibtex.migrated'):
                shutil.copyfile(self.from_path / 'better-bibtex.migrated',
                                self.to_path   / 'better-bibtex.migrated')

            else:
                self.state = 'ERROR'
                self.error_type = 'no betbib'

        else:
            self.state = 'ERROR'
            self.error_type = 'no file'

    def extract_valid_tables(self, path:Path) -> dict:
        """
        Function to extract all databse from the copied `.sqlite` files and
        store them under pandas.DataFrame in a dictionary.

        Parameters
        ----------
        path : pathlib.Path
            Access path to database.

        """
        # Connection to SQLite database copied in read-only mode
        connect = sqlite3.connect(f"file:{path}?mode=ro", uri=True)

        # Query to get list of all tables in database
        query = "SELECT name FROM sqlite_master WHERE type='table';"

        # Execute the query and fetch all results
        cursor = connect.cursor()

        cursor.execute(query)
        tables = cursor.fetchall()
        dico_tables = {}
        for table in tables:
            query_it = "SELECT * FROM "+table[0]

            # Uses pandas to execute the query and store data in a DataFrame
            df = pd.read_sql_query(query_it, connect)
            if len(df) > 0:
                dico_tables[table[0]] = df.copy()

        # Closes the connection to the database
        connect.close()

        return dico_tables

    def load_database(self) -> None:
        """
        Function to extract the databse and update associated parameters.
        """
        # Extracts data from the Zotero database
        path_data = self.to_path / 'zotero.sqlite'
        self.data = self.extract_valid_tables(path_data)

        # Extracts data from the Better BibTex database
        if os.path.isfile(self.to_path / 'better-bibtex.sqlite'):
            path_data = self.to_path / 'better-bibtex.sqlite'
        elif os.path.isfile(self.to_path / 'better-bibtex.migrated'):
            path_data = self.to_path / 'better-bibtex.migrated'
        
        self.data_cite_key = self.extract_valid_tables(path_data)
        self.data_cite_key = self.data_cite_key['citationkey']
        self.one_loaded = True
        self.load_sq.color = [0, 200, 0]
        if self.comp_st == 2:
            self.comp_sq.color = [242, 133, 0]
            self.comp_st = 1

    def treat_by_paper(self) -> None:
        """
        Function to extract usefull documents informations and pre compute
        some of ther caracteristics for optimisation.

        Informations extracted / used:
        keys[i]: str
            Beter bibtex citation key
            itemID: int
                ID of the document, used as a link with the creator table.
            itemKey: str
                Hash key where the files linked to the document are stored.
            parentItemID: int
                An other ID of the document to make the link between the
                tables.
            date: numpy.ndarray
                Array of dtype: datetime64[D] It is defined when the document
                was created.
            title: str
                The document title.
            firstName: list
                List of the authors first name.
            lastName: list
                List of the authors last name.
            firstName_uc: list
                List of the authors first name under no special caracter.
            lastName_uc: list
                List of the authors last name under no special caracter.

        """
        self.papers = {}
        self.authors = {}
        self.num_elem = len(self.data_cite_key)
        # better bibtex citation keys will be used as acces keys
        # for the dictionary
        keys = np.copy(self.data_cite_key.loc[:, 'citationKey'])
        for i in tqdm(range(self.num_elem)):
            self.papers[keys[i]] = {}
            # Various id linked to the document
            self.papers[keys[i]]['itemID'] = self.data_cite_key.loc[
                                                         i, 'itemID']

            self.papers[keys[i]]['itemKey'] = self.data_cite_key.loc[
                                                         i, 'itemKey']

            idx_par = np.argwhere(self.data['itemAttachments'].loc[:,
                                        'parentItemID'] == self.papers[
                                        keys[i]]['itemID'])[0, 0]

            self.papers[keys[i]]['parentItemID'] = self.data[
                               'itemAttachments'].loc[idx_par, 'itemID']

            # When the document was created in zotero
            idx_tim = np.argwhere(self.data['items'].loc[:, 'itemID'] ==
                                  self.papers[keys[i]]['parentItemID'])[0, 0]

            add_time = np.array([self.data['items'].loc[idx_tim,
                    'clientDateModified']], dtype='datetime64[s]')

            self.papers[keys[i]]['date'] = add_time.astype('datetime64[D]')

            # Get the tile of the document
            idx_dat = np.argwhere(
                self.data['itemData'].loc[:, 'itemID'] ==
                self.papers[keys[i]]['parentItemID'])[:, 0]

            for j in idx_dat:
                if self.data['itemData'].loc[j, 'fieldID'] == 1:
                    idx_tit = np.argwhere(
                        self.data['itemDataValues'].loc[:, 'valueID'] ==
                        self.data['itemData'].loc[j, 'valueID'])[0, 0]

                    self.papers[keys[i]]['title'] = self.data[
                        'itemDataValues'].loc[idx_tit, 'value']

            # Get the first and last name of the authors
            idx_item = np.argwhere(self.data['itemCreators'].loc[:,
                    'itemID'] == self.papers[keys[i]]['itemID'])[:, 0]

            self.papers[keys[i]]['firstName'] = []
            self.papers[keys[i]]['lastName'] = []
            self.papers[keys[i]]['firstName_uc'] = []
            self.papers[keys[i]]['lastName_uc'] = []
            for j in idx_item:
                idx_crea = np.argwhere(
                    self.data['creators'].loc[:, 'creatorID'] ==
                    self.data['itemCreators'].loc[j, 'creatorID'])[0, 0]

                fname = self.data['creators'].loc[idx_crea, 'firstName']
                lname = self.data['creators'].loc[idx_crea, 'lastName']
                self.papers[keys[i]]['firstName'].append(fname)
                self.papers[keys[i]]['lastName'].append(lname)
                self.papers[keys[i]]['firstName_uc'].append(unidecode(fname))
                self.papers[keys[i]]['lastName_uc'].append(unidecode(lname))

                # author oriented dictionary
                cle_aut = lname+', '+fname
                if cle_aut not in list(self.authors.keys()):
                    self.authors[cle_aut] = {}
                    self.authors[cle_aut]['date'] = self.papers[
                        keys[i]]['date']

                    self.authors[cle_aut]['citekeys'] = [] 
                    self.authors[cle_aut]['citekeys'].append(keys[i])

                    self.authors[cle_aut]['dispkeys'] = [] 
                    tx = self.TEXT_FONT.render(keys[i], 1, 'black')
                    if tx.get_width() < self.TXT_LEN[1]:
                        self.authors[cle_aut]['dispkeys'].append(keys[i])
                    else:
                        c = -1
                        while tx.get_width() > self.TXT_LEN[0]:
                            tx = self.TEXT_FONT.render(keys[i][:c], 1,
                                                       'black')
                            c -= 1

                        self.authors[cle_aut]['dispkeys'].append(
                                    keys[i][:c]+'...')

                    self.authors[cle_aut]['firstName'] = fname
                    self.authors[cle_aut]['lastName'] = lname
                    self.authors[cle_aut]['firstName_uc'] = unidecode(fname)
                    self.authors[cle_aut]['lastName_uc'] = unidecode(lname)

                else:
                    if keys[i] not in self.authors[cle_aut]['citekeys']:
                        self.authors[cle_aut]['citekeys'].append(keys[i])
                        tx = self.TEXT_FONT.render(keys[i], 1, 'black')
                        if tx.get_width() < self.TXT_LEN[1]:
                            self.authors[cle_aut]['dispkeys'].append(keys[i])
                        else:
                            c = -1
                            while tx.get_width() > self.TXT_LEN[0]:
                                tx = self.TEXT_FONT.render(keys[i][:c], 1,
                                                           'black')

                                c -= 1

                            self.authors[cle_aut]['dispkeys'].append(
                                        keys[i][:c]+'...')

                    if (self.papers[keys[i]]['date'] >
                            self.authors[cle_aut]['date']):

                        self.authors[cle_aut]['date'] = self.papers[
                            keys[i]]['date']

        # create 1d array for time comparison wich will be faster than loop
        authkeys = np.sort(list(self.authors.keys()))
        self.auth_time = np.zeros(len(authkeys), dtype='datetime64[D]')
        # if author first name have '.' in it
        self.auth_abv = np.zeros(len(authkeys), dtype=bool)
        # author last and first name length
        self.auth_len_last  = np.zeros(len(authkeys))
        self.auth_len_first = np.zeros(len(authkeys))
        # letters in authors last and first name
        self.bag_last = np.zeros((len(authkeys), 256), dtype='uint8')
        self.bag_first = np.zeros((len(authkeys), 256), dtype='uint8')
        c_l, c_f = 0, 0
        for i in range(len(authkeys)):
            self.auth_time[i] = self.authors[authkeys[i]]['date'][0]
            self.auth_abv[i] = '.' in self.authors[authkeys[i]]['firstName']

            l_red = self.reduce_string(self.authors[authkeys[i]]['lastName'])
            f_red = self.reduce_string(self.authors[authkeys[i]]['firstName'])

            self.auth_len_last[i]  = len(l_red)
            self.auth_len_first[i] = len(f_red)

            u_l, v_l = np.unique(list(l_red), return_counts=True)
            for j in range(len(u_l)):
                if u_l[j] not in self.letters['l']:
                    self.letters['l'][u_l[j]] = c_l
                    self.bag_last[i, c_l] = v_l[j]
                    c_l += 1
                else:
                    self.bag_last[i, c_l] = v_l[j]

            u_f, v_f = np.unique(list(f_red), return_counts=True)
            for j in range(len(u_f)):
                if u_f[j] not in self.letters['f']:
                    self.letters['f'][u_f[j]] = c_f
                    self.bag_first[i, c_f] = v_f[j]
                    c_f += 1
                else:
                    self.bag_first[i, c_f] = v_f[j]

        self.bag_last = self.bag_last[:, :c_l]
        self.bag_first = self.bag_first[:, :c_f]

    def preparation_matching(self) -> (np.ndarray, str, str):
        """
        Function to make the global first step for every mathing options.

        Returns
        -------
        mask_operations : numpy.ndarray
            Numpy 1 dimensional boolean array.
        firstName : str
            First name author.
        lastName : str
            Last name author.

        """
        # Compute time filtering using numpy.ndarray
        if self.to_filter == 'today':
            mask_time = self.auth_time >= self.today
        elif self.to_filter == 'tod-1w':
            mask_time = self.auth_time >= self.tod_1w
        elif self.to_filter == 'tod-1m':
            mask_time = self.auth_time >= self.tod_1m
        elif self.to_filter == 'tod-1y':
            mask_time = self.auth_time >= self.tod_1y

        w = len(self.auth_time)
        mask_square = np.triu(np.ones((w, w), dtype=bool), 1)
        mask_operations = np.ones(int(w**2/2-w/2), dtype=bool)

        # flat with the right way
        if self.to_filter != None:
            mask = mask_time & mask_time[:, None]
            mask_operations = mask_operations & mask[mask_square]

        if np.any(self.filter_abv):
            mask = self.auth_abv&self.auth_abv[:, None]
            mask_operations = mask_operations & mask[mask_square]

        if np.any(self.use_special):
            firstName = 'firstName' ; lastName = 'lastName'
        else:
            # First and Last names without special caracters,
            # removed with unicode.unicode
            firstName = 'firstName_uc' ; lastName = 'lastName_uc'

        if self.to_compare == 'lastname':
            # Ignore the case if one of the author didn't give its last name
            # (not seen in my corpus of size 3,734)
            mask = (self.auth_len_last>0)&(self.auth_len_last[:, None]>0)
            mask_operations = mask_operations & mask[mask_square]

        elif self.to_compare == 'firstname':
            # Ignore the case if an author didn't give its first name (i.e.:
            # organisations, anonymous, some indonesian authors...)
            mask = (self.auth_len_first>0)&(self.auth_len_first[:, None]>0)
            mask_operations = mask_operations & mask[mask_square]

        if self.algo == 'Levenshtein' or self.algo == 'DamerauLevenshtein':
            # for Damerau-Levenshtein, I need to implement a safer parameter
            # due to transposition matrix test
            if (self.to_compare == 'firstname'):
                prescore = np.minimum(
                    self.auth_len_last[:, None], self.auth_len_last
                    ) / np.maximum(
                    self.auth_len_last[:, None], self.auth_len_last)

                mask = prescore > self.treshold
                pre_d = cdist(self.bag_last, self.bag_last,
                              metric='cityblock') / 2 / np.maximum(
                    self.auth_len_last[:, None], self.auth_len_last
                    ) <= self.treshold

            elif (self.to_compare == 'lastname'):
                prescore = np.minimum(
                    self.auth_len_first[:, None], self.auth_len_first
                    ) / np.maximum(
                    self.auth_len_first[:, None], self.auth_len_first)

                mask = prescore > self.treshold
                pre_d = cdist(self.bag_first, self.bag_first,
                              metric='cityblock') / 2 / np.maximum(
                    self.auth_len_last[:, None], self.auth_len_last
                    ) <= self.treshold

            elif (self.to_compare == 'bothname'):
                prescore_f = np.minimum(
                    self.auth_len_first[:, None], self.auth_len_first
                    ) / np.maximum(
                    self.auth_len_first[:, None], self.auth_len_first)

                prescore_l = np.minimum(
                    self.auth_len_last[:, None], self.auth_len_last
                    ) / np.maximum(
                    self.auth_len_last[:, None], self.auth_len_last)

                pre_f = cdist(self.bag_first, self.bag_first,
                    metric='cityblock') / 2 / np.maximum(
                    self.auth_len_first[:, None], self.auth_len_first)

                pre_l = cdist(self.bag_last, self.bag_last,
                    metric='cityblock') / 2 / np.maximum(
                    self.auth_len_last[:, None], self.auth_len_last)

                if self.both_comp == 'AND':
                    mask = (prescore_f > self.treshold)&(
                            prescore_l > self.treshold)

                    pre_d = (pre_f <= self.treshold)&(pre_l <= self.treshold)

                elif self.both_comp == 'OR':
                    mask = (prescore_f > self.treshold)|(
                            prescore_l > self.treshold)

                    pre_d = (pre_f <= self.treshold)|(pre_l <= self.treshold)

                elif self.both_comp == 'AVG':
                    mask = ((prescore_f+prescore_l)/2) > self.treshold
                    pre_d = (pre_f + pre_l) / 2 <= self.treshold

            mask_operations = mask_operations & mask[mask_square]
            mask_operations = mask_operations & pre_d[mask_square]

        # Re-Initialisation
        self.liste1 = [] ; self.liste2 = [] ; self.light = []

        return mask_operations, firstName, lastName

    def update_comparison(self, authkeys_i:str, authkeys_j:str, color:bool
                          ) -> bool:
        """
        Function to add citation keys if asked.

        Parameters
        ----------
        authkeys_i : dict
            First author.
        authkeys_j : dict
            Second author.
        color : bool
            If the line is white (False) or grey (True).

        Returns
        -------
        not color : bool
            If the line is white (False) or grey (True).

        """
        if np.any(self.add_key):
            # if the better bibtex citation key
            k1 = self.authors[authkeys_i]['dispkeys']
            k2 = self.authors[authkeys_j]['dispkeys']
            l1 = len(k1) ; l2 = len(k2)
            if l1 == l2:
                for l in range(l1):
                    self.liste1.append(k1[l])
                    self.liste2.append(k2[l])
                    self.light.append(color)

            elif l1 > l2:
                for l in range(l1):
                    self.liste1.append(k1[l])
                    self.light.append(color)
                    if l < l2:
                        self.liste2.append(k2[l])
                    else:
                        self.liste2.append(' ')

            elif l1 < l2:
                for l in range(l2):
                    self.liste2.append(k2[l])
                    self.light.append(color)
                    if l < l1:
                        self.liste1.append(k1[l])
                    else:
                        self.liste1.append(' ')

        self.liste1.append(' ')
        self.liste2.append(' ')
        self.light.append(color)

        return not color

    def clean_Lev_strings(self, string_1:str, string_2:str
                          ) -> (np.ndarray, np.ndarray):
        """
        Function to transform and filter some characters of the strings used
        to compute Levenshtein and Damerau-Levenshtein distance.

        Parameters
        ----------
        string_1 : str
            First string.
        string_2 : str
            Secind string.

        Returns
        -------
        arr_str_1 : np.ndarray
            Numpy 1 dimensional string ndarray.
        arr_str_2 : np.ndarray
            Numpy 1 dimensional string ndarray.

        """
        arr_str_1 = np.array(list(self.reduce_string(string_1)))
        arr_str_2 = np.array(list(self.reduce_string(string_2)))
        return arr_str_1, arr_str_2

    def Levenshtein_distance(self, string_1:str, string_2:str) -> float:
        """
        Levenshtein distance function.

        Parameters
        ----------
        string_1 : str
            First string.
        string_2 : str
            Secind string.

        Returns
        -------
        float
            Levenshtein distance.

        """
        arr_str_1, arr_str_2 = self.clean_Lev_strings(string_1, string_2)
        len1, len2 = len(arr_str_1), len(arr_str_2)
        dist = np.zeros((len1+1, len2+1))
        dist[0] = np.arange(0, len2+1, 1)
        dist[:, 0] = np.arange(0, len1+1, 1)
        dist[1:, 1:] = (arr_str_1[:, None] != arr_str_2).astype(int)
        for i in range(2, len1+len2+1):
            i_indices = np.arange(max(1, i - len2), min(i, len1 + 1))
            j_indices = i - i_indices
            dist[i_indices, j_indices] = np.min([
                dist[i_indices-1, j_indices  ] + 1,
                dist[i_indices  , j_indices-1] + 1,
                dist[i_indices-1, j_indices-1] + dist[i_indices, j_indices]],
                axis=0)

        return dist[-1, -1] / max([len1, len2])

    def Levenshtein_distance_es(self, string_1:str, string_2:str) -> float:
        """
        Levenshtein distance function with treshold based early stoping.

        Parameters
        ----------
        string_1 : str
            First string.
        string_2 : str
            Secind string.

        Returns
        -------
        float
            Levenshtein distance with 1.0 when early stoping is triggered.

        """
        arr_str_1, arr_str_2 = self.clean_Lev_strings(string_1, string_2)
        len1, len2 = len(arr_str_1), len(arr_str_2)
        dist = np.zeros((len1+1, len2+1))
        dist[0] = np.arange(0, len2+1, 1)
        dist[:, 0] = np.arange(0, len1+1, 1)
        dist[1:, 1:] = (arr_str_1[:, None] != arr_str_2).astype(int)
        maxim = max([len1, len2])
        runned = True
        for i in range(2, len1+len2+1):
            i_indices = np.arange(max(1, i-len2), min(i, len1+1))
            j_indices = i - i_indices
            minim = np.min([
                dist[i_indices-1, j_indices  ] + 1,
                dist[i_indices  , j_indices-1] + 1,
                dist[i_indices-1, j_indices-1] + dist[i_indices, j_indices]],
                 axis=0)

            if (np.min(minim)/maxim) > self.treshold:
                runned = False
                break

            else:
                dist[i_indices, j_indices] = minim

        if runned:
            return dist[-1, -1] / maxim
        else:
            return 1.

    def Damerau_Levenshtein(self, string_1:str, string_2:str):
        """
        Function to compute Damerau-Levenshtein distance.

        Parameters
        ----------
        string_1 : str
            First string.
        string_2 : str
            Secind string.

        Returns
        -------
        float
            Damerau-Levenshtein distance.

        """
        arr_str_1, arr_str_2 = self.clean_Lev_strings(string_1, string_2)

        len1 = len(arr_str_1)
        len2 = len(arr_str_2)
        dist = np.zeros((len1+1, len2+1))
        dist[0] = np.arange(0, len2+1, 1)
        dist[:, 0] = np.arange(0, len1+1, 1)
        dist[1:, 1:] = (arr_str_1[:, None] != arr_str_2).astype(int)
    
        for i in range(2, len1+len2+1):
            i_indices = np.arange(max(1, i - len2), min(i, len1 + 1))
            j_indices = i - i_indices
            dist[i_indices, j_indices] = np.min([
                dist[i_indices-1, j_indices  ] + 1,
                dist[i_indices  , j_indices-1] + 1,
                dist[i_indices-1, j_indices-1] + dist[i_indices, j_indices]],
                axis=0)
    
            if i > 2:
                mask = (i_indices > 1)&(j_indices > 1)
                i_p2 = i_indices[mask] ; j_p2 = j_indices[mask]
    
                mask = (arr_str_1[i_p2-1] == arr_str_2[j_p2-2])&(
                        arr_str_1[i_p2-2] == arr_str_2[j_p2-1])
    
                if np.any(mask):
                    dist[i_p2[mask], j_p2[mask]] = np.min([
                        dist[i_p2[mask]  , j_p2[mask]  ],
                        dist[i_p2[mask]-2, j_p2[mask]-2]+1], axis=0)
    
        return dist[-1, -1] / max(len1, len2)
    
    def Damerau_Levenshtein_es(self, string_1:str, string_2:str):
        """
        Function to compute Damerau-Levenshtein distance with early stoping.

        Parameters
        ----------
        string_1 : str
            First string.
        string_2 : str
            Secind string.

        Returns
        -------
        float
            Damerau-Levenshtein distance with 1.0 if the early stoping is
            triggered.

        """
        arr_str_1, arr_str_2 = self.clean_Lev_strings(string_1, string_2)
    
        len1 = len(arr_str_1)
        len2 = len(arr_str_2)
        dist = np.zeros((len1+1, len2+1))
        dist[0] = np.arange(0, len2+1, 1)
        dist[:, 0] = np.arange(0, len1+1, 1)
        dist[1:, 1:] = (arr_str_1[:, None] != arr_str_2).astype(int)
        maxim = max(len1, len2)
        runned = True
        for i in range(2, len1+len2+1):
            i_indices = np.arange(max(1, i - len2), min(i, len1 + 1))
            j_indices = i - i_indices
            dist[i_indices, j_indices] = np.min([
                dist[i_indices-1, j_indices  ] + 1,
                dist[i_indices  , j_indices-1] + 1,
                dist[i_indices-1, j_indices-1] + dist[i_indices, j_indices]],
                axis=0)
    
            if i > 2:
                mask = (i_indices > 1)&(j_indices > 1)
                i_p2 = i_indices[mask] ; j_p2 = j_indices[mask]
    
                mask = (arr_str_1[i_p2-1] == arr_str_2[j_p2-2])&(
                        arr_str_1[i_p2-2] == arr_str_2[j_p2-1])
    
                if np.any(mask):
                    dist[i_p2[mask], j_p2[mask]] = np.min([
                        dist[i_p2[mask]  , j_p2[mask]  ],
                        dist[i_p2[mask]-2, j_p2[mask]-2]+1], axis=0)
    
            if ((np.min(dist[i_indices, j_indices])-1.)/maxim) >self.treshold:
                runned = False
                break
    
        if runned:
            return dist[-1, -1] / maxim
        else:
            return 1.0

    def record_matching(self, val_a1:str, val_a2:str, val_b1:str, val_b2:str,
                        color:bool) -> None:
        """
        Function to append matching results into the comparison list.

        Parameters
        ----------
        val_a1 : str
            First part of the author name. Can be first or last name.
        val_a2 : str
            Second part of the author name. Can be first or last name.
        val_b1 : str
            First part of the author name. Can be first or last name.
        val_b2 : str
            Second part of the author name. Can be first or last name.
        color : bool
            If the background line is white (False) or grey (True).

        """
        self.liste1.append(val_a1+', '+val_a2)
        self.liste2.append(val_b1+', '+val_b2)
        self.light.append(color)

    def comparison_matching(self) -> None:
        """
        Function to compute the comparison between each authors pair.
        """
        # Global precomputing
        mask_operations, firstName, lastName = self.preparation_matching()

        if self.algo == 'Perfect':
            is_match = lambda a, b: a == b

        else:
            # for optimisation use early stoping version whe treshold < 0.
            if self.algo == 'Levenshtein':
                # for optimisation use early stoping version whe treshold < 0.74
                if self.treshold >= 0.74:
                    f_dist = self.Levenshtein_distance
                else:
                    f_dist = self.Levenshtein_distance_es
    
            elif self.algo == 'DamerauLevenshtein':
                if self.treshold >= 0.72:
                    f_dist = self.Damerau_Levenshtein_distance
                else:
                    f_dist = self.Damerau_Levenshtein_distance_es

            is_match = lambda a, b: f_dist(a, b) <= self.treshold

        c_idx = 0
        color = False
        authkeys = np.sort(list(self.authors.keys()))
        num_aut = len(authkeys)
        pbar = tqdm(total=len(mask_operations))
        for i in range(num_aut-1):
            auth_1 = self.authors[authkeys[i]]
            for j in range(i+1, num_aut):
                auth_2 = self.authors[authkeys[j]]
                c_s2 = self.authors[authkeys[j]][firstName]
                c_n2 = self.authors[authkeys[j]][lastName]
                same = False
                if mask_operations[c_idx]:
                    # Last / First name comparison
                    if self.to_compare == 'lastname':
                        if is_match(auth_1[lastName], auth_2[lastName]):
                            same = True
                            self.record_matching(
                                auth_1[lastName], auth_1[firstName],
                                auth_2[lastName], auth_2[firstName], color)

                    elif self.to_compare == 'firstname':
                        if is_match(auth_1[firstName], auth_2[firstName]):
                            same = True
                            self.record_matching(
                                auth_1[firstName], auth_1[lastName],
                                auth_2[firstName], auth_2[lastName], color)

                    elif self.to_compare == 'bothname':
                        d_l = f_dist(auth_1[lastName], auth_2[lastName])
                        d_f = f_dist(auth_1[firstName], auth_2[firstName])
                        if self.both_comp == 'AND':
                            # if one True => == 1.0 else == 0.0
                            d = float((d_l > self.treshold) or
                                      (d_f > self.treshold))

                        elif self.both_comp == 'OR':
                            d = float((d_l > self.treshold) and
                                      (d_f > self.treshold))

                        elif self.both_comp == 'AVG':
                            d = (d_l+d_f)/2

                        if d <= self.treshold:
                            same = True
                            self.record_matching(
                                auth_1[lastName], auth_1[firstName],
                                auth_2[lastName], auth_2[firstName], color)

                c_idx += 1
                if same:
                    color = self.update_comparison(authkeys[i], authkeys[j],
                                                   color)

                pbar.update(1)

    def export_comparaison(self) -> None:
        """
        Function to save the computed comparison in a csv file.
        """
        df = pd.DataFrame()
        df['liste_1'] = self.liste1
        df['liste_2'] = self.liste2
        if self.to_path != '':
            df.to_csv(self.to_path / 'exported_comparison.csv', index=False)

    def export_db2json(self) -> None:
        """
        Function to save the used database into json file.
        """
        if len(self.papers) <= 0:
            self.state = 'ERROR'
            self.error_type = 'no compil'
            
        else:
            # Compute time filtering using numpy.ndarray
            if self.to_filter == 'today':
                mask_time = self.auth_time >= self.today
            elif self.to_filter == 'tod-1w':
                mask_time = self.auth_time >= self.tod_1w
            elif self.to_filter == 'tod-1m':
                mask_time = self.auth_time >= self.tod_1m
            elif self.to_filter == 'tod-1y':
                mask_time = self.auth_time >= self.tod_1y

            self.papers_save = {}
            keys = list(self.papers.keys())
            if self.to_filter != None:
                for i in range(len(keys)):
                    if mask_time[i]:
                        paper = self.papers[keys[i]]
                        self.papers_save[keys[i]] = {}
                        self.papers_save[keys[i]]['title'] = self.papers[
                            keys[i]]['title']

                        self.papers_save[keys[i]]['added_date'] = str(
                            self.papers[keys[i]]['date'])[2:-2]

                        self.papers_save[keys[i]]['lastName'] = self.papers[
                            keys[i]]['lastName']

                        self.papers_save[keys[i]]['firstName'] = self.papers[
                            keys[i]]['firstName']

            else:
                for i in range(len(keys)):
                    paper = self.papers[keys[i]]
                    self.papers_save[keys[i]] = {}
                    self.papers_save[keys[i]]['title'] = self.papers[
                        keys[i]]['title']

                    self.papers_save[keys[i]]['added_date'] = str(
                        self.papers[keys[i]]['date'])[2:-2]

                    self.papers_save[keys[i]]['lastName'] = self.papers[
                        keys[i]]['lastName']

                    self.papers_save[keys[i]]['firstName'] = self.papers[
                        keys[i]]['firstName']

            try:
                with open(self.to_path / 'exported_db.json', "w",
                          encoding="utf-8") as file:

                    json.dump(self.papers_save, file, indent=4)

            except IOError as e:
                print(f"Error saving dictionary: {e}")

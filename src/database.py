
import os
import json
import shutil
import pygame
import sqlite3
import numpy as np
import pandas as pd
import configparser
from time import time
from pathlib import Path
from unidecode import unidecode

# Object to manage the buttons
from buttons import Button_selection, Button_app_actions, Text, Inidication

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
        self.to_compare = None               # 'lastname' ou 'firstname'
        self.to_filter = None                # 'today', 'tod-1w', etc.
        self.use_special = np.array([False]) # Keep or not the accents
        self.filter_abv = np.array([False])  # Use only or not abreviations
        self.add_key = np.array([False])     # Render citation keys

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
        # Database loading button
        self.load_db_bt = Button_app_actions(
            x_start=np.array([ 25]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([ 50]) * self.SCALE,
            y_stop =np.array([ 90]) * self.SCALE,
            text=np.array(['(Re)Load database']),
            font=self.TEXT_FONT, lin_w=3,
            target='load_db_manager', bt_color=self.bt_color)

        # Database compile button
        self.compile_db_bt = Button_app_actions(
            x_start=np.array([ 25]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([100]) * self.SCALE,
            y_stop =np.array([140]) * self.SCALE,
            text=np.array(['Compile the database']),
            font=self.TEXT_FONT, lin_w=3,
            target='compile_database', bt_color=self.bt_color)

        # How the authors will be compared buttons
        self.comparaison_bt = Button_selection(
            x_start=np.array([ 45, 245]) * self.SCALE,
            x_stop =np.array([155, 355]) * self.SCALE,
            y_start=np.array([180, 180]) * self.SCALE,
            y_stop =np.array([220, 220]) * self.SCALE,
            text=np.array(['Last name', 'First name']),
            font=self.TEXT_FONT, lin_w=3, target='to_compare',
            values=np.array(['lastname', 'firstname']),
            empty_sel=None, colors=[(20, 250, 75), self.bt_color])

        # Filter on the date of the documents addition buttons
        self.time_filter_bt = Button_selection(
            x_start=np.array([ 40, 240,  40, 240]) * self.SCALE,
            x_stop =np.array([160, 360, 160, 360]) * self.SCALE,
            y_start=np.array([255, 255, 305, 305]) * self.SCALE,
            y_stop =np.array([295, 295, 345, 345]) * self.SCALE,
            text=np.array(['Today', '-1 week', '-1 month', '-1 year']),
            font=self.TEXT_FONT, lin_w=3, target='to_filter',
            values=np.array(['today', 'tod-1w', 'tod-1m', 'tod-1y']),
            empty_sel=None, colors=[(20, 250, 75), self.bt_color])

        # If the abbreviation are used to filter button
        self.abbreviation_bt = Button_selection(
            x_start=np.array([ 40]) * self.SCALE,
            x_stop =np.array([160]) * self.SCALE,
            y_start=np.array([355]) * self.SCALE,
            y_stop =np.array([395]) * self.SCALE,
            text=np.array(['Abreviation']), font=self.TEXT_FONT, lin_w=3,
            target='filter_abv', values=np.array([True]),
            empty_sel=np.array([False]),
            colors=[(20, 250, 75), self.bt_color])

        # If the "special" letters are used or not (é -> e) button
        self.special_letter_bt = Button_selection(
            x_start=np.array([240]) * self.SCALE,
            x_stop =np.array([360]) * self.SCALE,
            y_start=np.array([355]) * self.SCALE,
            y_stop =np.array([395]) * self.SCALE,
            text=np.array(['Special']), font=self.TEXT_FONT, lin_w=3,
            target='use_special', values=np.array([True]),
            empty_sel=np.array([False]), colors=[(20, 250, 75), (255, 0, 0)])

        # If Better bibtex citation keys are displayed button
        self.add_keys_bt = Button_selection(
            x_start=np.array([ 75]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([405]) * self.SCALE,
            y_stop =np.array([445]) * self.SCALE,
            text=np.array(['Display the citation key']),
            font=self.TEXT_FONT, lin_w=3, target='add_key',
            values=np.array([True]), empty_sel=np.array([False]),
            colors=[(20, 250, 75), self.bt_color])

        # Compare first/last name of the authors button
        self.show_computed_bt = Button_app_actions(
            x_start=np.array([ 75]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([470]) * self.SCALE,
            y_stop =np.array([510]) * self.SCALE,
            text=np.array(['Show']), font=self.TEXT_FONT, lin_w=3,
            target='compute_show', bt_color=self.bt_color)

        # To reset parameters button
        self.reset_param_bt = Button_app_actions(
            x_start=np.array([ 75]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([520]) * self.SCALE,
            y_stop =np.array([560]) * self.SCALE,
            text=np.array(['Reset']), font=self.TEXT_FONT,
            lin_w=3, target='reinit', bt_color=self.bt_color)

        # To export the comparison between authors button
        self.export_comparaison_bt = Button_app_actions(
            x_start=np.array([ 75]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([570]) * self.SCALE,
            y_stop =np.array([610]) * self.SCALE,
            text=np.array(['Export comparaison']),
            font=self.TEXT_FONT, lin_w=3,
            target='compute_export_show', bt_color=self.bt_color)

        # To export the database into a json file button
        self.export_db_json_bt = Button_app_actions(
            x_start=np.array([ 75]) * self.SCALE,
            x_stop =np.array([325]) * self.SCALE,
            y_start=np.array([630]) * self.SCALE,
            y_stop =np.array([670]) * self.SCALE,
            text=np.array(['Export db as json']),
            font=self.TEXT_FONT, lin_w=3,
            target='export_jsonf', bt_color=self.bt_color)

        # All buttons list
        self.all_buttons = [
            self.load_db_bt, self.compile_db_bt, self.comparaison_bt,
            self.time_filter_bt, self.abbreviation_bt, self.special_letter_bt,
            self.add_keys_bt, self.show_computed_bt, self.reset_param_bt,
            self.export_comparaison_bt, self.export_db_json_bt]

        # Text fields
        self.title_txt = Text([200*self.SCALE]*4, np.array([20, 200, 275,
            325])*self.SCALE, ['Manager', '/', '/', '/'], self.TITLE_FONT)

        self.texte_txt = Text([200*self.SCALE]*2, np.array([165, 240]
            )*self.SCALE, ['Compare by :', 'Filter by :'], self.TEXT_FONT)

        # Loading state square
        self.load_sq = Inidication([342.5*self.SCALE, 50*self.SCALE,
                                    40*self.SCALE, 40*self.SCALE], [200,0,0])
        # Compilation state square
        self.comp_sq = Inidication([342.5*self.SCALE, 100*self.SCALE,
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
         'no file': {'text':[
           'No database was found from the given access path, make',
            'sure you writte the correct path in the "main.ini" file.',
            'Given path:', str(self.from_path)],
          'y_center':y_centers},

         'no betbib': {'text':[
           'No Better-BibTex database was found from the given access path,',
           'make sure you writte the correct path in the "main.ini" file.',
           'Given path:', str(self.from_path)],
          'y_center':y_centers},

         'no database': {'text':[
           "No database has yet been imported, merged into one with:",
           "'(Re)Load database' before trying to compile."],
          'y_center':y_centers[:2]},

         'no compil': {'text':[
           "The loaded database has not yet been compiled. Compile it with:",
           "'Compile the database' before trying to use it."],
          'y_center':y_centers[:2]},

         'no compar': {
          'text':[
           "You need to choose how the authors will compare using the ",
           "buttons: 'Last name' / 'First name'."],
          'y_center':y_centers[:2]}}

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
        path_data = self.to_path / 'better-bibtex.sqlite'
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
        for i in range(self.num_elem):
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
        #self.auth_abv = np.zeros(len(authkeys))
        for i in range(len(authkeys)):
            self.auth_time[i] = self.authors[authkeys[i]]['date'][0]

    def comparison_by(self) -> None:
        """
        Function to compute the authors comparison through the various
        parameters choiced in the UI.
        """
        # Compute time filtering using numpy.ndarray
        if self.to_filter == 'today':
            mask_time = self.auth_time < self.today
        elif self.to_filter == 'tod-1w':
            mask_time = self.auth_time < self.tod_1w
        elif self.to_filter == 'tod-1m':
            mask_time = self.auth_time < self.tod_1m
        elif self.to_filter == 'tod-1y':
            mask_time = self.auth_time < self.tod_1y

        # flat with the right way
        if self.to_filter != None:
            mask_time = mask_time & mask_time[:, np.newaxis]
            mask_time = mask_time[(np.arange(len(self.auth_time)) -
                                   np.arange(len(self.auth_time))[:,
                                       np.newaxis]) > 0]

        if np.any(self.use_special):
            firstName = 'firstName'
            lastName = 'lastName'
        else:
            # First and Last names without special caracters,
            # removed with unicode.unicode
            firstName = 'firstName_uc'
            lastName = 'lastName_uc'

        c_idx = 0
        self.liste1 = []
        self.liste2 = []
        self.light = []
        color = False
        authkeys = np.sort(list(self.authors.keys()))
        num_aut = len(authkeys)
        for i in range(num_aut-1):
            c_s1 = self.authors[authkeys[i]][firstName]
            c_n1 = self.authors[authkeys[i]][lastName]
            if np.any(self.filter_abv):
                abb_s1 = '.' not in c_s1

            for j in range(i+1, num_aut):
                c_s2 = self.authors[authkeys[j]][firstName]
                c_n2 = self.authors[authkeys[j]][lastName]
                to_comp = True
                same = False
                # Time filtering
                if self.to_filter != None:
                    if mask_time[c_idx]:
                        to_comp = False

                    c_idx +=1

                if to_comp:
                    if np.any(self.filter_abv):
                        if abb_s1&('.' not in c_s2):
                            to_comp = False

                if to_comp:
                    # Last / First name comparison
                    if self.to_compare == 'lastname':
                        if c_n1 == c_n2:
                            same = True
                            self.liste1.append(c_n1+', '+c_s1)
                            self.liste2.append(c_n2+', '+c_s2)
                            self.light.append(color)

                    elif self.to_compare == 'firstname':
                        if c_s1 == c_s2:
                            same = True
                            self.liste1.append(c_s1+', '+c_n1)
                            self.liste2.append(c_s2+', '+c_n2)
                            self.light.append(color)

                if same:
                    if np.any(self.add_key):
                        # if the better bibtex citation key
                        k1 = self.authors[authkeys[i]]['dispkeys']
                        k2 = self.authors[authkeys[j]]['dispkeys']
                        l1 = len(k1)
                        l2 = len(k2)
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

                    color = ~ color

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


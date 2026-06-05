
import pygame
import numpy as np
from time import time

# For string distances
import distances

# Object to manage the buttons
from buttons import (Button_selection, Button_app_actions, Text, Inidication,
                     Button_keyboard, Scroll_barr)

pygame.init()

class Config:
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
        # Vertical space for each line of text
        self.text_height = 30 *self.SCALE
        # Maximum number of lines visible in the comparison panel
        self.mx_tx = int(self.HEIGHT / self.text_height)
        # text lenght limits
        self.TXT_LEN = [380*self.SCALE, 385*self.SCALE]
        # comparison pannel limits
        self.COMP_LINES  = [785*self.SCALE, 790*self.SCALE, 800*self.SCALE]
        # x comparison text position
        self.COMP_TX_X   = [405*self.SCALE, 795*self.SCALE]
        # y offset comparison text
        self.COMP_TX_DY  = 5*self.SCALE
        # Comparison feilds x midle line division
        self.DIVIDERS = 790*self.SCALE
        self.prog_bar = False    # If a progression bar is render
        self.index = 0           # Index of iteration bar
        self.tot_idx = 1         # last index of the iteration bar
        # second part of progression bar text
        self.max_i_blit = self.TITLE_FONT.render('/ 1', 1, 'black')
        self.max_i_pos  = (0, 0) # where to draw the max iter num
        # first part of progression bar text
        self.idx_blit = self.TITLE_FONT.render('0', 1, 'black')
        self.idx_pos = (0, 0)    # where to draw the current iter

        # Progression bar
        self.st_pb = 110 * self.SCALE
        self.sp_pb = 1080 * self.SCALE
        self.h_pb = 450*self.SCALE-20*self.SCALE
        self.l_pb = 450*self.SCALE+20*self.SCALE
        self.width_pb = self.sp_pb - self.st_pb
        self.pb_line = [[self.st_pb, self.h_pb], [self.st_pb, self.l_pb],
                        [self.sp_pb, self.h_pb], [self.sp_pb, self.l_pb]]

        self.prog_box = np.array([self.st_pb, self.h_pb, 0, 40*self.SCALE])
        # refresh rate of the progression bar in milliseconds
        self.refresh_rate = int(self.FPS * 2)

        # white empty box
        self.box_tx = [400*self.SCALE, 0, 800*self.SCALE, self.HEIGHT]

        # --- Gestion de l'État ---
        self.state = 'IDLE'  # IDLE, LOADING, COMPUTING, ERROR, etc.
        self.error_type = '' # For the error type gestion
        self.comp_st = 0     # Compilation state (0: empty, 1: loaded,
        #                       2: compiled)

        # --- Paths and files ---
        self.from_path = '' # origin path of the databse
        self.to_path = ''   # path where to copy the database

        # --- Data structur ---
        self.data = {}             # raw Zotero tables
        self.data_cite_key = {}    # Better-BibTeX citation keys
        self.one_loaded = False    # True if db has been successfully loaded
        self.use_zotero_db = False # Better-BibTex and zotero db has fused

        self.papers = {}      # Indexed by Citation Key
        self.authors = {}     # Indexed par first and last name
        self.num_elem = 0     # Total number of documents

        # --- Comparison parameters (with buttons interactions) ---
        self.to_compare = None # 'lastname', 'firstname' or 'bothname'
        self.to_filter = None  # 'today', 'tod-1w', etc.
        self.treshold = 0.10   # treshold value for distance based algorithm
        self.max_len  = 1      # maximum length for distance based algorithm

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

        self.time_filter = {
            'today' : self.today      , # today
            'tod_1w': self.today -   7, # today minus one week
            'tod_1m': self.today -  31, # today minus one month
            'tod_1y': self.today - 365  # today minus one year
            }

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
            x_start=np.array([ 80,  80,  80,  80,  80]) *self.SCALE,
            x_stop =np.array([320, 320, 320, 320, 320]) *self.SCALE,
            y_start=np.array([180, 230, 280, 330, 380]) *self.SCALE,
            y_stop =np.array([220, 270, 320, 370, 420]) *self.SCALE,
            text=np.array(['Perfect', 'Levenshtein rel',
                           'Damerau-Levenshtein rel', 'Levenshtein abs',
                           'Damerau-Levenshtein abs']),
            font=self.TEXT_FONT, lin_w=3, target='algo',
            values=np.array(['Perfect', 'Levenshtein_rel',
                             'DamerauLevenshtein_rel', 'Levenshtein_abs',
                             'DamerauLevenshtein_abs']),
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

        # Buttons list for the Levenshtein relative distance algorithm
        self.levenshtein_rel_bt = [
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

        # Buttons list for the Levenshtein absolute distance algorithm
        self.levenshtein_abs_bt = [
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
            text='1', font=self.TEXT_FONT, lin_w=2,
            target='max_len', bounds=[0, np.inf]),

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

        # Buttons list for the Demarau-Levenshtein relative distance algorithm
        self.D_levenshtein_rel_bt = [
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

        # Buttons list for the Demarau-Levenshtein relative distance algorithm
        self.D_levenshtein_abs_bt = [
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
            text='1', font=self.TEXT_FONT, lin_w=2,
            target='max_len', bounds=[0, np.inf]),
        
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

        self.dists_bts = {
            'Levenshtein_rel':self.levenshtein_rel_bt,
            'DamerauLevenshtein_rel':self.levenshtein_abs_bt,
            'Levenshtein_abs':self.D_levenshtein_abs_bt,
            'DamerauLevenshtein_abs':self.D_levenshtein_abs_bt}

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

        self.scroller = Scroll_barr(
            box=np.array([1180*self.SCALE, 0, 20*self.SCALE, self.HEIGHT]),
            colors=[(255, 255, 255), self.bt_color, (0, 0, 0)],
            lin_w=3)

        # Which tab to show
        self.pannel = 'DATA' # DATA, SETTINGS, EXECUTION

        # Wich algorithm is choose
        self.algo = None # Perfect, Levenshtein, DamerauLevenshtein

        # Text fields
        self.matching_txt = Text([200*self.SCALE]*3, np.array([75, 120, 170]
            )*self.SCALE, ['Compare by:', '/', 'Filters:'], self.TITLE_FONT)

        self.levenshtein_rel_txt = Text(np.array([200, 130, 270, 200, 150, 185,
            130, 270])*self.SCALE, np.array([75, 120, 120, 180, 280, 380, 420,
            420])*self.SCALE, ['To use:', '/', '/', 'Transform:',
            'Maximum distance:', 'Reduction for both name:', '/', '/'],
            self.TITLE_FONT)

        self.levenshtein_abs_txt = Text(np.array([200, 130, 270, 200, 150, 185,
            130, 270])*self.SCALE, np.array([75, 120, 120, 180, 280, 380, 420,
            420])*self.SCALE, ['To use:', '/', '/', 'Transform:',
            'Maximum distance:', 'Reduction for both name:', '/', '/'],
            self.TITLE_FONT)

        self.dam_lev_rel_txt = Text(np.array([200, 130, 270, 200, 150, 185, 130,
            270])*self.SCALE, np.array([75, 120, 120, 180, 280, 380, 420, 420]
            )*self.SCALE, ['To use:', '/', '/', 'Transform:',
            'Maximum distance:', 'Reduction for both name:', '/', '/'],
            self.TITLE_FONT)

        self.dam_lev_abs_txt = Text(np.array([200, 130, 270, 200, 150, 185, 130,
            270])*self.SCALE, np.array([75, 120, 120, 180, 280, 380, 420, 420]
            )*self.SCALE, ['To use:', '/', '/', 'Transform:',
            'Maximum distance:', 'Reduction for both name:', '/', '/'],
            self.TITLE_FONT)

        self.dists_txts = {
            'Levenshtein_rel':self.levenshtein_rel_txt,
            'DamerauLevenshtein_rel':self.levenshtein_rel_txt,
            'Levenshtein_abs':self.dam_lev_abs_txt,
            'DamerauLevenshtein_abs':self.dam_lev_abs_txt}

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
           'Given path:', str(self.to_path)],
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

        # Warm-Up for numba.njit acceleration
        warmup_1 = np.array(['a', 'b', 'c', 'd', 'e'])
        warmup_2 = np.array(['f', 'g', 'h', 'i', 'j'])

        distances.Levenshtein_rel_dist(warmup_1, warmup_2)
        distances.Damerau_Levenshtein_rel_dist(warmup_1, warmup_2)
        distances.Levenshtein_abs_dist(warmup_1, warmup_2)
        distances.Damerau_Levenshtein_abs_dist(warmup_1, warmup_2)

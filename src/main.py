
import pygame
import numpy as np
import pandas as pd
from time import time
from pathlib import Path
from buttons import Button_selection, Button_keyboard

# Object to manage the database from duplicate to interaction
from database import DataGest

pygame.init()

class Manager(DataGest):
    """
    Main GUI Manager for the Zotero authors application.
    Inherits from DataGest to handle backend data logic while managing
    the Pygame interface, user inputs, and visual states.
    """

    def __init__(self) -> None:
        """
        Initializes the Manager, sets up the Pygame window and UI state
        variables.
        """

        super().__init__()

        self.window = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption('Zotero Author Duplicate Detector')

        # UI State flag
        self.m_text = False     # True if mouse over the text panel

        # Data display variables
        self.tex_y = 0     # Scroll index (which row starts the display)
        self.delta_txy = 0 # Number of rows currently visible

        # Warm-Up for numba.njit acceleration
        warmup_1 = np.array(['a', 'b', 'c', 'd', 'e'])
        warmup_2 = np.array(['f', 'g', 'h', 'i', 'j'])
        self.Levenshtein_distance_es(warmup_1, warmup_2)
        self.Damerau_Levenshtein_distance_es(warmup_1, warmup_2)

    def reinit(self) -> None:
        """
        Resets the application state, clearing all loaded data and UI positions.
        Used when loading a new database or restarting the process.
        """
        self.one_loaded = False
        self.m_text = False
        self.prog_bar = False
        self.index = 0

        self.load_sq.color = [200, 0, 0]
        self.comp_sq.color = [200, 0, 0]

        # Path and counters
        self.from_path = ''
        self.to_path = ''
        self.num_elem = 0

        # State Machine
        self.state = 'IDLE'
        self.algo = None
        self.error_type = ''

        # Data structures
        self.comp_st = 0
        self.papers = {}
        self.authors = {}
        self.auth_time = np.zeros(0)
        self.auth_abv = np.zeros(0)
        self.auth_len_last  = np.zeros(0)
        self.auth_len_first = np.zeros(0)
        self.letters   = {'l':{}, 'f':{}}
        self.bag_last  = np.zeros(0)
        self.bag_first = np.zeros(0)

        self.to_compare = None
        self.to_filter = None

        # Comparison lists for the display panel
        self.liste1 = []
        self.liste2 = []
        self.light = []

        # Scrollbar reset
        self.bscroll[1] = max([1, 3 * self.SCALE])
        self.bscroll[3] = 692 * self.SCALE
        self.tex_y = 0
        self.delta_txy = 0

        # Time handling for filters
        self.today = np.array([time()]).astype('datetime64[s]').astype(
            'datetime64[D]')

        self.tod_1w = self.today-7
        self.tod_1m = self.today-31
        self.tod_1y = self.today-365

        # Reset button selection states
        for button in self.data_buttons:
            if type(button) == Button_selection:
                button.selected[:] = False

        for button in self.matching_bt:
            if type(button) == Button_selection:
                button.selected[:] = False

        for button in self.levenshtein_bt:
            if type(button) == Button_selection:
                button.selected[:] = False
            elif type(button) == Button_keyboard:
                button.selected = False

        for button in self.D_levenshtein_bt:
            if type(button) == Button_selection:
                button.selected[:] = False
            elif type(button) == Button_keyboard:
                button.selected = False

        for button in self.execution_bt:
            if type(button) == Button_selection:
                button.selected[:] = False

        self.use_special = np.array([False])
        self.filter_abv = np.array([False])
        self.add_key = np.array([False])
        self.both_comp = 'AND'

        # Dynamic update of error message content
        self.error_messages['no file']['text'][3] = str(self.from_path)
        self.error_messages['no betbib']['text'][3] = str(self.from_path)

    def mouse_over_params(self) -> None:
        """
        Detects if the mouse is over the control panel (right) or the text
        panel (left). Updates button hover states accordingly.
        """
        if self.mouse_pos[0] > self.COMP_TX_X[0]:
            # set the buttons to False
            self.m_text = True
        else:
            self.m_text = False

        # Check interaction for all buttons in the control area
        self.pannels_bt.test_mouse(self.mouse_pos)
        if self.pannel == 'DATA':
            for button in self.data_buttons:
                button.test_mouse(self.mouse_pos)

        elif self.pannel == 'SETTINGS':
            if self.algo == 'Perfect':
                for button in self.matching_bt:
                    button.test_mouse(self.mouse_pos)

            elif self.algo == 'Levenshtein':
                for button in self.levenshtein_bt:
                    button.test_mouse(self.mouse_pos)

            elif self.algo == 'DamerauLevenshtein':
                for button in self.D_levenshtein_bt:
                    button.test_mouse(self.mouse_pos)

        elif self.pannel == 'EXECUTION':
            for button in self.execution_bt:
                button.test_mouse(self.mouse_pos)

    def mouse_wheel(self, event:pygame.event.Event) -> None:
        """
        Handles mouse wheel events for scrolling through comparison panels and
        updates the display's vertical scroll positions.

        Parameters
        ----------
        event : pygame.event.Event
            The mouse wheel event object. It's expected to have 'y' attribute
            indicating scroll direction (1 for up, -1 for down).

        """
        n_gene = len(self.liste1)
        if self.m_text:
            if (event.y != 0)&(n_gene > self.mx_tx_y):
                # Determine scroll direction and update the vertical text
                # offset indexe (self.tex_y)
                if event.y == 1:
                    self.tex_y = max([self.tex_y-event.y, 0])
                else: # == -1
                    self.tex_y = min([self.tex_y-event.y,
                                      n_gene-self.mx_tx_y])

                # Update the position of the scrollbar thumb (self.bscroll[1])
                # based on the new vertical text offset. It scales the scrol-
                # -lbar position proportionally to the text's scroll position.
                self.bscroll[1] = (max([1, 3 * self.SCALE]) +
                                   self.tex_y * self.text_height *
                                   (self.mx_tx_y / n_gene))

                # Calculate the number of lines currently printed in
                # comparison panel
                if (n_gene - self.tex_y) >= self.mx_tx_y:
                    self.delta_txy = self.mx_tx_y
                else:
                    self.delta_txy = (n_gene - self.tex_y)

    def load_db_manager(self) -> None:
        """
        Triggered by the load button. Orchestrates the file duplication 
        and database loading sequence.
        """
        self.state = 'LOADING'
        self.draw() # Force draw to show loading screen
        self.duplicate_table()
        if self.state != 'ERROR':
            self.load_database()
            self.state = 'IDLE'

        self.draw()

    def compile_database(self) -> None:
        """
        Processes the raw database into structured papers/authors dictionaries.
        Sets the compilation status (comp_st) to green (2) upon success.
        """
        if self.one_loaded:
            self.state = 'COMPUTING'
            self.draw()
            self.treat_by_paper(self)
            self.state = 'IDLE'
            self.comp_st = 2
            self.comp_sq.color = [0, 200, 0]

        else:
            self.m_text = False
            self.state = 'ERROR'
            self.error_type = 'no database'

    def comparaison_bt_error_management(self) -> None:
        """
        Checks for prerequisites before allowing a comparison to run. Sets
        error states if database is missing, not compiled, or mode is
        unselected.
        """
        if not self.one_loaded:
            self.m_text = False
            self.state = 'ERROR'
            self.error_type = 'no database'

        if self.one_loaded & (len(self.papers) == 0):
            self.m_text = False
            self.state = 'ERROR'
            self.error_type = 'no compil'

        elif (len(self.papers) > 0)&(self.to_compare == None):
            self.m_text = False
            self.state = 'ERROR'
            self.error_type = 'no compar'

        elif self.algo == 'Levenshtein':
            for button in self.levenshtein_bt:
                if type(button) == Button_keyboard:
                    button.test_errors(self)

        elif self.algo == 'DamerauLevenshtein':
            for button in self.D_levenshtein_bt:
                if type(button) == Button_keyboard:
                    button.test_errors(self)

    def compute_show(self) -> None:
        """
        Runs the comparison logic and calculates UI parameters for the
        newly generated result list (scrollbar height, scroll index).
        """
        self.comparaison_bt_error_management()
        if self.one_loaded & (self.state != 'ERROR'):
            self.state = 'COMPARING'
            self.m_text = False
            self.draw()
            if self.algo == 'Levenshtein':
                for button in self.levenshtein_bt:
                    if type(button) == Button_keyboard:
                        self.treshold = float(button.temp)

            elif self.algo == 'DamerauLevenshtein':
                for button in self.D_levenshtein_bt:
                    if type(button) == Button_keyboard:
                        self.treshold = float(button.temp)

            self.comparison_matching(self)
            self.state = 'IDLE'
            self.tex_y = 0 # Reset scroll to top
            n_gene = len(self.liste1)

            # Adjust scrollbar geometry for the new list length
            if n_gene > self.mx_tx_y:
                self.bscroll[1] = (max([1, 3 * self.SCALE]) +
                                   self.tex_y * self.text_height *
                                   (self.mx_tx_y / n_gene))

                # Scale scrollbar thumb (min 15 pixels for usability)
                self.bscroll[3] = (692 * self.SCALE * self.mx_tx_y / n_gene
                                   ) if (n_gene < 1000) else 15*self.SCALE

            # Refresh display boundaries
            if (n_gene-self.tex_y) >= self.mx_tx_y:
                self.delta_txy = self.mx_tx_y
            else:
                self.delta_txy = (n_gene-self.tex_y)

    def compute_export_show(self) -> None:
        """
        Ensures comparison results exist before triggering the CSV export.
        """
        if len(self.liste1) > 0:
            # Show was already computed
            pass
        else:
            # Show wasn't already computed
            self.compute_show()

        if self.one_loaded & (self.state != 'ERROR'):
            self.state = 'EXPORTING'
            self.m_text = False
            self.draw()
            self.export_comparaison()
            self.state = 'IDLE'

    def export_jsonf(self) -> None:
        """
        Handles the export of the database to a JSON format.
        """
        self.state = 'EXPORTING'
        self.m_text = False
        self.draw()
        if not self.one_loaded:
            self.state = 'ERROR'
            self.error_type = 'no database'
        else:
            self.export_db2json()
            if self.state != 'ERROR':
                self.state = 'IDLE'

    def mouse_gestion_clic(self) -> None:
        """
        Distributes click events to the appropriate buttons based on current
        state. Dismisses error messages on click.
        """
        if self.state == 'ERROR':
            self.state = 'IDLE'
            self.error_type = ''

        elif self.state == 'IDLE':
            self.pannels_bt.actions(self)
            if self.pannel == 'DATA':
                for button in self.data_buttons:
                    button.actions(self)

            elif self.pannel == 'SETTINGS':
                if self.algo == 'Perfect':
                    for button in self.matching_bt:
                        button.actions(self)

                elif self.algo == 'Levenshtein':
                    for button in self.levenshtein_bt:
                        if type(button) == Button_keyboard:
                            button.actions_click()
                        else:
                            button.actions(self)

                elif self.algo == 'DamerauLevenshtein':
                    for button in self.D_levenshtein_bt:
                        if type(button) == Button_keyboard:
                            button.actions_click()
                        else:
                            button.actions(self)

            elif self.pannel == 'EXECUTION':
                for button in self.execution_bt:
                    button.actions(self)

    def gestion_keyboard(self, event:pygame.event.Event) -> None:
        """
        Function to handle interaction between keybord actions and the
        selected keyboard button.

        Parameters
        ----------
        event : pygame.event.Event
            Pygame event beeing a keybord action.

        """
        if self.state == 'IDLE':
            if self.pannel == 'SETTINGS':
                if self.algo == 'Levenshtein':
                    for button in self.levenshtein_bt:
                        if type(button) == Button_keyboard:
                            button.actions_keyboard(event)

                elif self.algo == 'DamerauLevenshtein':
                    for button in self.D_levenshtein_bt:
                        if type(button) == Button_keyboard:
                            button.actions_keyboard(event)

    def draw_data_pannel(self) -> None:
        """
        Function to render the data gestion pannel. To load and compile the
        databse and to choose the comparison algorithm.
        """
        # Load Status indicator
        self.load_sq.draw(self.window)

        # Compilation Status indicator
        #     red: not compiled
        #     orange: compiled database but a new one was imported
        #     green: compiled and no new loaded
        self.comp_sq.draw(self.window)
        for button in self.data_buttons:
            button.draw(self.window)

    def draw_settings_pannel(self) -> None:
        """
        Function to render the settings pannel. To define algorithm settingd.
        """
        if self.algo == 'Perfect':
            self.matching_txt.draw(self.window)
            for button in self.matching_bt:
                button.draw(self.window)

        elif self.algo == 'Levenshtein':
            self.levenshtein_txt.draw(self.window)
            for button in self.levenshtein_bt:
                button.draw(self.window)

        elif self.algo == 'DamerauLevenshtein':
            self.dam_lev_txt.draw(self.window)
            for button in self.D_levenshtein_bt:
                button.draw(self.window)

    def draw_execution_pannel(self) -> None:
        """
        Function to render the buttons and text of the execution pannel.
        """
        self.execution_txt.draw(self.window)
        for button in self.execution_bt:
            button.draw(self.window)

    def draw_comparisons(self) -> None:
        """
        Function to render the result of the author comparision.
        """
        if self.state not in self.waiting_messages:
            c = 0
            for i in range(self.tex_y, self.tex_y+self.delta_txy):
                if self.light[i]:
                    pygame.draw.rect(self.window, self.bt_color,
                        (self.box_tx[0], c*self.text_height, self.box_tx[2],
                         self.text_height))
    
                tx = self.TEXT_FONT.render(self.liste1[i], 1, 'black')
                self.window.blit(tx, (self.COMP_TX_X[0],
                                      self.COMP_TX_DY+self.text_height*c))
    
                tx = self.TEXT_FONT.render(self.liste2[i], 1, 'black')
                self.window.blit(tx, (self.COMP_TX_X[1],
                                      self.COMP_TX_DY+self.text_height*c))
    
                c += 1

        # --- SCROLLBAR AREA ---
        pygame.draw.rect(self.window, 'white', self.fscroll)
        if len(self.liste1) > self.mx_tx_y:
            # The scrollbar thumb
            pygame.draw.rect(self.window, self.bt_color, self.bscroll)

        # Outlines and dividers
        pygame.draw.rect(self.window, (0, 0, 0), self.box_tx, 2)
        # scorll box
        pygame.draw.rect(self.window, (0, 0, 0), self.fscroll, 2)
        # midle line
        pygame.draw.line(self.window, (0, 0, 0), (self.DIVIDERS, 0),
                         (self.DIVIDERS, self.HEIGHT), 2)

    def draw_main_interface(self) -> None:
        """
        Renders the static and dynamic parts of the main UI:
        1. Comparison results (left panel)
        2. Scrollbar (middle divider)
        3. Control buttons and status indicators (right panel)
        """
        # --- RIGHT PANEL: Results List ---
        pygame.draw.rect(self.window, 'white', self.box_tx)
        # Draw background highlights for "light" flagged entries
        # Render the two strings to be compared side-by-side
        self.draw_comparisons()

        # --- Controls pannels ---
        # Tab buttons
        self.pannels_bt.draw(self.window)
        # Tab separation
        pygame.draw.line(self.window, 'black', (self.pannels_bt.x_stop[0], 0),
            (self.pannels_bt.x_stop[0], self.pannels_bt.y_stop[0]), 3)

        pygame.draw.line(self.window, 'black', (self.pannels_bt.x_stop[1], 0),
            (self.pannels_bt.x_stop[1], self.pannels_bt.y_stop[1]), 3)

        if self.pannel == 'DATA':
            pygame.draw.line(self.window, 'black',
                (self.pannels_bt.x_stop[0], self.pannels_bt.y_stop[0]),
                (self.pannels_bt.x_stop[2], self.pannels_bt.y_stop[2]), 3)

            self.draw_data_pannel()

        elif self.pannel == 'SETTINGS':
            pygame.draw.line(self.window, 'black',
                (self.pannels_bt.x_start[0], self.pannels_bt.y_stop[0]),
                (self.pannels_bt.x_stop[0], self.pannels_bt.y_stop[0]), 3)

            pygame.draw.line(self.window, 'black',
                (self.pannels_bt.x_start[2], self.pannels_bt.y_stop[2]),
                (self.pannels_bt.x_stop[2], self.pannels_bt.y_stop[2]), 3)

            self.draw_settings_pannel()

        elif self.pannel == 'EXECUTION':
            pygame.draw.line(self.window, 'black',
                (self.pannels_bt.x_start[0], self.pannels_bt.y_stop[0]),
                (self.pannels_bt.x_stop[1], self.pannels_bt.y_stop[1]), 3)

            self.draw_execution_pannel()

    def draw_text_msg(self, text:str, center_y:int) -> None:
        """
        Helper method to render centered text on the screen.

        Parameters
        ----------
        text : str
            The string to display.
        center_y : int
            The vertical center position for the text.

        """
        tx_f = self.TITLE_FONT.render(text, 1, 'black')
        self.window.blit(tx_f, (600 * self.SCALE-tx_f.get_width()/2,
                                center_y-tx_f.get_height()/2))

    def draw_error(self) -> None:
        """
        Renders an overlay window containing error details when state is
        'ERROR'.
        """
        box = np.array([100, 100, 1000, 500]) * self.SCALE
        pygame.draw.rect(self.window, self.bt_color, box)
        pygame.draw.rect(self.window, (0, 0, 0), box, 3)
        self.draw_text_msg('Warning !', 250 * self.SCALE)
        message = self.error_messages[self.error_type]
        for i in range(len(message['text'])):
            self.draw_text_msg(message['text'][i], message['y_center'][i])

    def draw_waiting_screen(self, message:str) -> None:
        """
        Renders a simple overlay with a message during long computations.

        Parameters
        ----------
            message: The string to display (e.g., "Computing...").

        """
        box = np.array([100, 100, 1000, 500]) * self.SCALE
        pygame.draw.rect(self.window, self.bt_color, box)
        pygame.draw.rect(self.window, (0, 0, 0), box, 3)
        self.draw_text_msg(message, 300 * self.SCALE)
        if self.prog_bar:
            # The progression bar
            pygame.draw.line(self.window, 'black', self.pb_line[0],
                             self.pb_line[1], 2)

            pygame.draw.line(self.window, 'black', self.pb_line[2],
                             self.pb_line[3], 2)

            pygame.draw.rect(self.window, 'black', self.prog_box)
            # The text of the progression bar
            self.idx_blit = self.TEXT_FONT.render(str(self.index), 1, 'black')
            self.idx_pos[0] = 595*self.SCALE-self.idx_blit.get_width()

            self.window.blit(self.idx_blit, self.idx_pos)
            self.window.blit(self.max_i_blit, self.max_i_pos)

    def draw(self) -> None:
        """
        Primary draw loop. Handles clearing the screen and deciding
        which overlay (Error, Waiting, or Main UI) to render.
        """
        self.window.fill(self.bg_color)
        self.draw_main_interface()
        if self.state == 'ERROR':
            self.draw_error()
        elif self.state in self.waiting_messages:
            self.draw_waiting_screen(self.waiting_messages[self.state])

        pygame.display.update()

    def main(self) -> None:
        """
        Application entry point. Contains the main event loop.
        """
        clock = pygame.time.Clock()
        self.run = True
        while self.run:
            clock.tick(self.FPS)
            self.mouse_pos = pygame.mouse.get_pos()

            # Update hover states only if no error is blocking the UI
            if self.state != 'ERROR':
                self.mouse_over_params()
    
            for event in pygame.event.get():
                # Click handling (ignoring wheel as click)
                if event.type == pygame.QUIT:
                    self.run = False
                    break

                # Scroll handling
                if (event.type == pygame.MOUSEBUTTONDOWN)&(
                    event.type != pygame.MOUSEWHEEL):
                    self.mouse_gestion_clic()
    
                if event.type == pygame.MOUSEWHEEL:
                    self.mouse_wheel(event)

                elif event.type == pygame.KEYDOWN:
                    self.gestion_keyboard(event)
    
            self.draw()
    
        pygame.quit()

if __name__ == '__main__':
    manager = Manager()
    manager.main()

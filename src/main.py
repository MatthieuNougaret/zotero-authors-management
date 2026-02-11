
import pygame
import numpy as np
import pandas as pd
from time import time
from pathlib import Path

# Object to manage the database from duplicate to interaction
from database import DataGest

pygame.init()

class Manager(DataGest):
    """
    Main GUI Manager for the Zotero authors application.
    Inherits from DataGest to handle backend data logic while managing
    the Pygame interface, user inputs, and visual states.
    """

    # window shape
    WIDTH, HEIGHT = 1200, 700

    # Frame Per Seconds
    FPS = 60

    # Colors
    bg_color = (245, 245, 213)  # Cream background
    bt_color = (180, 180, 180)  # Grey for buttons/panels

    # UI Constants
    mx_tx_y = 23     # Max number of lines visible in the comparison panel
    text_height = 30 # Vertical space for each line of text
    b_l_init = 692   # Initial pixel length of the scrollbar

    def __init__(self) -> None:
        """
        Initializes the Manager, sets up the Pygame window and UI state
        variables.
        """

        super().__init__()

        self.window = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption('Zotero Author Duplicate Detector')

        # UI State flags
        self.m_text = False     # True if mouse over the text panel
        self.one_loaded = False # True if db has been successfully loaded

        # Data display variables
        self.barr_len = self.b_l_init # initial length of the vertical bar
        self.y_barr = 3    # Current Y position of the scrollbar thumb
        self.tex_y = 0     # Scroll index (which row starts the display)
        self.delta_txy = 0 # Number of rows currently visible

    def reinit(self) -> None:
        """
        Resets the application state, clearing all loaded data and UI positions.
        Used when loading a new database or restarting the process.
        """
        self.one_loaded = False
        self.m_text = False

        # Path and counters
        self.from_path = ''
        self.to_path = ''
        self.num_elem = 0

        # State Machine
        self.state = 'IDLE'
        self.error_type = ''

        # Data structures
        self.comp_st = 0
        self.papers = {}
        self.authors = {}
        self.auth_time = np.zeros(0)
        self.auth_abv = np.zeros(0)

        self.to_compare = None
        self.to_filter = None

        # Comparison lists for the display panel
        self.liste1 = []
        self.liste2 = []
        self.light = []

        # Scrollbar reset
        self.barr_len = self.b_l_init
        self.y_barr = 3
        self.tex_y = 0
        self.delta_txy = 0

        # Time handling for filters
        self.today = np.array([time()]).astype('datetime64[s]').astype(
            'datetime64[D]')

        self.tod_1w = self.today-7
        self.tod_1m = self.today-31
        self.tod_1y = self.today-365

        # Reset button selection states
        self.use_special = np.array([False])
        self.filter_abv = np.array([False])
        self.add_key = np.array([False])
        self.comparaison_bt.selected[:] = False
        self.time_filter_bt.selected[:] = False
        self.abbreviation_bt.selected[:] = False
        self.special_letter_bt.selected[:] = False
        self.add_keys_bt.selected[:] = False

        # Dynamic update of error message content
        self.error_messages['no file']['text'][3] = str(self.from_path)
        self.error_messages['no betbib']['text'][3] = str(self.from_path)

    def mouse_over_params(self) -> None:
        """
        Detects if the mouse is over the control panel (right) or the text
        panel (left). Updates button hover states accordingly.
        """
        if self.mouse_pos[0] >= 800:
            self.m_text = False
            # Check interaction for all buttons in the control area
            for button in self.all_buttons:
                button.test_mouse(self.mouse_pos)

        else:
            # Mouse is over the comparison panel
            self.m_text = True

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

                # Update the position of the scrollbar thumb (y_barr) based
                # on the new vertical text offset. It scales the scrollbar
                # position proportionally to the text's scroll position.
                self.y_barr = (3 + self.tex_y * self.text_height * (
                    self.mx_tx_y / n_gene))

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
            self.treat_by_paper()
            self.state = 'IDLE'
            self.comp_st = 2

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
            self.comparison_by()
            self.state = 'IDLE'
            self.tex_y = 0 # Reset scroll to top
            n_gene = len(self.liste1)

            # Adjust scrollbar geometry for the new list length
            if n_gene > self.mx_tx_y:
                self.y_barr = (3 + self.tex_y * self.text_height * (
                    self.mx_tx_y / n_gene))

                # Scale scrollbar thumb (min 15 pixels for usability)
                self.barr_len = (self.b_l_init * self.mx_tx_y / n_gene
                                 ) if (n_gene < 1000) else 15

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
            # Test all buttons actions
            for button in self.all_buttons:
                button.actions(self)

    def draw_main_interface(self) -> None:
        """
        Renders the static and dynamic parts of the main UI:
        1. Comparison results (left panel)
        2. Scrollbar (middle divider)
        3. Control buttons and status indicators (right panel)
        """
        # --- LEFT PANEL: Results List ---
        c = 0
        pygame.draw.rect(self.window, 'white', (0, 0, 800, self.HEIGHT))

        # Draw background highlights for "light" flagged entries
        for i in range(self.tex_y, self.tex_y+self.delta_txy):
            if self.light[i]:
                pygame.draw.rect(self.window, self.bt_color,
                                 (0, c*self.text_height, 800, self.text_height))

            c += 1

        # Render the two strings to be compared side-by-side
        c = 0
        for i in range(self.tex_y, self.tex_y+self.delta_txy):
            tx = self.TEXT_FONT.render(self.liste1[i], 1, 'black')
            self.window.blit(tx, (5, 5+self.text_height*c))

            tx = self.TEXT_FONT.render(self.liste2[i], 1, 'black')
            self.window.blit(tx, (394, 5+self.text_height*c))
            c += 1

        # --- SCROLLBAR AREA ---
        pygame.draw.rect(self.window, 'white', (780, 0, 20, self.HEIGHT))
        if len(self.liste1) > self.mx_tx_y:
            # The scrollbar thumb
            pygame.draw.rect(self.window, self.bt_color,
                             (781,  self.y_barr, 18, self.barr_len))

            # Bottom boundary indicator
            pygame.draw.rect(self.window, (0, 0, 0), (781,  694, 18, 5))

        # Outlines and dividers
        pygame.draw.rect(self.window, (0, 0, 0), (0, 0, 800, self.HEIGHT), 2)
        pygame.draw.rect(self.window, (0, 0, 0), (780, 0, 20, self.HEIGHT), 2)
        pygame.draw.line(self.window, (0, 0, 0), (389, 0), (389, self.HEIGHT), 2)

        # --- RIGHT PANEL: Controls ---
        tx = self.TITLE_FONT.render('Manager', 1, 'black')
        self.window.blit(tx, (1000-tx.get_width()/2, 10))
        # Load Status indicator
        if self.one_loaded:
            pygame.draw.rect(self.window, (0, 200, 0), (1142.5, 50, 40, 40))
        else:
            pygame.draw.rect(self.window, (200, 0, 0), (1142.5, 50, 40, 40))

        # Compilation Status indicator
        #     red: not compiled
        #     orange: compiled database but a new one was imported
        #     green: compiled and no new loaded
        if self.comp_st == 0:
            pygame.draw.rect(self.window, (200, 0, 0), (1142.5, 100, 40, 40))
        elif self.comp_st == 1:
            pygame.draw.rect(self.window, (242, 133, 0), (1142.5, 100, 40, 40))
        elif self.comp_st == 2:
            pygame.draw.rect(self.window, (0, 200, 0), (1142.5, 100, 40, 40))

        # # UI Text Labels
        tx = self.TEXT_FONT.render('Compare by :', 1, 'black')
        self.window.blit(tx, (1000-tx.get_width()/2, 165-tx.get_height()/2))

        # Layout separators
        ts = self.TITLE_FONT.render('/', 1, 'black')
        self.window.blit(ts, (1000-ts.get_width()/2, 200-ts.get_height()/2))
        self.window.blit(ts, (1000-ts.get_width()/2, 275-ts.get_height()/2))
        self.window.blit(ts, (1000-ts.get_width()/2, 325-ts.get_height()/2))

        tx = self.TEXT_FONT.render('Filter by :', 1, 'black')
        self.window.blit(tx, (1000-tx.get_width()/2, 240-tx.get_height()/2))

        # Call individual draw methods for all button objects
        for button in self.all_buttons:
            button.draw(self.window)

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
        self.window.blit(tx_f, (600-tx_f.get_width()/2,
                                center_y-tx_f.get_height()/2))

    def draw_error(self) -> None:
        """
        Renders an overlay window containing error details when state is
        'ERROR'.
        """
        pygame.draw.rect(self.window, self.bt_color, (100, 100, 1000, 500))
        pygame.draw.rect(self.window, (0, 0, 0), (100, 100, 1000, 500), 3)
        self.draw_text_msg('Warning !', 250)
        message = self.error_messages[self.error_type]

        for i in range(len(message['text'])):
            self.draw_text_msg(message['text'][i], message['y_center'][i])

    def draw_waiting_screen(self, message:str):
        """
        Renders a simple overlay with a message during long computations.

        Parameters
        ----------
            message: The string to display (e.g., "Computing...").

        """
        pygame.draw.rect(self.window, self.bt_color, (100, 100, 1000, 500))
        pygame.draw.rect(self.window, (0, 0, 0), (100, 100, 1000, 500), 3)
        self.draw_text_msg(message, 350)

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
        run = True
        while run:
            clock.tick(self.FPS)
            self.mouse_pos = pygame.mouse.get_pos()

            # Update hover states only if no error is blocking the UI
            if self.state != 'ERROR':
                self.mouse_over_params()
    
            for event in pygame.event.get():
                # Click handling (ignoring wheel as click)
                if event.type == pygame.QUIT:
                    run = False
                    break

                # Scroll handling
                if (event.type == pygame.MOUSEBUTTONDOWN)&(
                    event.type != pygame.MOUSEWHEEL):
                    self.mouse_gestion_clic()
    
                if event.type == pygame.MOUSEWHEEL:
                    self.mouse_wheel(event)
    
            self.draw()
    
        pygame.quit()

if __name__ == '__main__':
    manager = Manager()
    manager.main()

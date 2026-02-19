
import pygame
import numpy as np
from time import time

pygame.init()

class Button:
    """
    General parent button class utilizing NumPy for vectorized state
    management. This class can handle multiple visual instances
    (buttons) simultaneously.

    Parameters
    ----------
    x_start : np.ndarray
        X position of the left corners.
    x_stop : np.ndarray
        X position of the right corners.
    y_start : np.ndarray
        Y position of the top corners.
    y_stop : np.ndarray
        Y position of the bottom corners.
    text : np.ndarray
        Array of strings to display on each button.
    font : pygame.font.SysFont
        Pygame font object for text rendering.
    lin_w : int
        Thickness of the border line when hovered.

    """

    def __init__(self,
                 x_start:np.ndarray,
                 x_stop:np.ndarray,
                 y_start:np.ndarray,
                 y_stop:np.ndarray,
                 text:np.ndarray,
                 font:pygame.font.SysFont,
                 lin_w:int) -> None:

        self.x_start = x_start
        self.x_stop = x_stop
        self.y_start = y_start
        self.y_stop = y_stop
        self.text = text
        self.font = font
        self.lin_w = lin_w
        self.number = len(self.x_start)

        # Vectorized calculation of centers and drawing boxes [x, y, width,
        #  height]
        self.center = np.array([(x_start+x_stop)/2,
                                (y_start+y_stop)/2]).T.tolist()

        # Boolean mask to track if mouse is hovering over each specific button
        self.draw_box = np.array([x_start, y_start,
                                  x_stop-x_start, y_stop-y_start]).T.tolist()

        # Pre-rendering text surfaces for better performance
        self.is_mouse_on = np.zeros(self.number, dtype=bool)
        self.text_blit = []
        self.text_blit_pos = []
        for i in range(self.number):
            self.text_blit.append(
                self.font.render(self.text[i], 1,'black'))

            # Centering the text surface on the button center
            self.text_blit_pos.append([
                self.center[i][0]-self.text_blit[i].get_width()/2,
                self.center[i][1]-self.text_blit[i].get_height()/2])

    def test_mouse(self, mouse_pos:tuple) -> None:
        """
        Updates the 'is_mouse_on' boolean mask using vectorized comparison.

        Parameters
        ----------
        mouse_pos : tuple
            Current (x, y) coordinates of the mouse.

        """
        self.is_mouse_on = (mouse_pos[0] >= self.x_start)&(
                            mouse_pos[1] >= self.y_start)&(
                            mouse_pos[0] <= self.x_stop )&(
                            mouse_pos[1] <= self.y_stop )


class Button_selection(Button):
    """
    Subclass for toggle-style buttons (Radio buttons). Only one button in
    the set can be active, or none.

    Parameters
    ----------
    target : str
        The name of the attribute in the 'app' object to update.
    values : np.ndarray
        The values to assign to the target when a button is selected.
    empty_sel : Any
        The value to assign if no button is selected.
    colors : list
        List of two RGB: [color_selected, color_not_selected].

    """
    def __init__(self, x_start, x_stop, y_start, y_stop, text, font, lin_w,
                 target:str,
                 values:np.ndarray,
                 empty_sel:type(None) | bool,
                 colors:list) -> None:

        super().__init__(x_start, x_stop, y_start, y_stop, text, font, lin_w)

        self.target = target
        self.values = values
        self.empty_sel = empty_sel
        self.colors = colors
        self.selected = np.zeros(self.number, dtype=bool)

    def actions(self, app) -> None:
        """
        Handles the selection logic: toggles the clicked button and updates
        the parent application's state.

        Parameters
        ----------
        app : Manager(DataGest)
            Class to update its attribute.

        """
        if np.any(self.is_mouse_on):
            # Toggles selection: if it was selected, unselect. If not, select
            # it. Only affects the button under the mouse.
            self.selected = (~self.selected) & self.is_mouse_on

            # Update the application attribute using reflection (setattr)
            if np.any(self.selected):
                setattr(app,self.target, str((self.values[self.selected])[0]))
            else:
                setattr(app, self.target, self.empty_sel)

    def draw(self, window:pygame.surface.Surface) -> None:
        """
        Renders all selection buttons with appropriate colors based on state.

        Parameters
        ----------
        window : pygame.surface.Surface
            Pygame surface object where buttons are draw.

        """
        for i in range(self.number):
            # Pick color based on selection state
            if self.selected[i]:
                pygame.draw.rect(window, self.colors[0], self.draw_box[i])
            else:
                pygame.draw.rect(window, self.colors[1], self.draw_box[i])

            # Draw a black border if hovered
            if self.is_mouse_on[i]:
                pygame.draw.rect(window, 'black', self.draw_box[i],
                                 self.lin_w)

            window.blit(self.text_blit[i], self.text_blit_pos[i])


class Button_app_actions(Button):
    """
    Subclass for action buttons that trigger a method call in the main app.
    Typically used for single buttons like 'Load', 'Compile', or 'Export'.

    Parameters
    ----------
    target : str
        The name of the attribute in the 'app' object to update.
    bt_color : list
        List of RGB values of button color.

    """
    def __init__(self, x_start, x_stop, y_start, y_stop, text, font, lin_w,
                 target:str,
                 bt_color:list):

        super().__init__(x_start, x_stop, y_start, y_stop, text, font, lin_w)

        self.target = target
        self.bt_color = bt_color

    def actions(self, app):
        """
        Calls the method specified by 'target' on the app instance.

        Parameters
        ----------
        app : Manager(DataGest)
            Class to update its attribute.

        """
        if np.any(self.is_mouse_on):
            # Retrieve the method from the app object and execute it
            method = getattr(app, self.target)
            method()

    def draw(self, window:pygame.surface.Surface) -> None:
        """
        Renders the action button.

        Parameters
        ----------
        window : pygame.surface.Surface
            Pygame surface object where buttons are draw.

        """
        pygame.draw.rect(window, self.bt_color, self.draw_box[0])
        # Border feedback on hover
        if self.is_mouse_on[0]:
            pygame.draw.rect(window, 'black', self.draw_box[0], self.lin_w)

        window.blit(self.text_blit[0], self.text_blit_pos[0])


class Button_keyboard(Button):
    """
    Button class for interactive keyboard-input button for numerical data
    entry within a Pygame application.

    Parameters
    ----------
    x_start : numpy.ndarray
        Vector with int or float of the starting x-coordinate of the button.
    x_stop : numpy.ndarray
        Vector with int or float of the ending x-coordinate of the button.
    y_start : numpy.ndarray
        Vector with int or float of the starting y-coordinate of the button.
    y_stop : numpy.ndarray
        Vector with int or float of the ending y-coordinate of the button.
    text : numpy.ndarray
        Vector with str of the initial text/value displayed on the button.
    font : pygame.font.Font
        The font object used to render the text.
    lin_w : int
        The line width for the button's border.
    target : str
        The identifier for the variable or setting this button modifies.
    bounds : list
        A list or tuple defining the [min, max] allowed numerical values.

    """
    def __init__(self, x_start, x_stop, y_start, y_stop, text, font, lin_w,
                 target:str,
                 bounds:list):

        super().__init__(x_start, x_stop, y_start, y_stop, text, font, lin_w)

        self.target = target
        self.bounds = bounds

        self.selected = False
        self.temp = self.text
        self.repre = np.array(list(self.text)).astype(object)
        self.cursor_idx = len(self.repre)
        self.center = self.center[0]
        self.draw_box = self.draw_box[0]

        self.text_blit = self.font.render(self.temp, 1, 'black')
        self.text_blit_pos = [self.center[0]-self.text_blit.get_width()/2,
                              self.center[1]-self.text_blit.get_height()/2]

        self.xy_cursor = [self.text_blit_pos[0]+self.text_blit.get_width(),
                          self.y_start[0]+4, self.y_stop[0]-4]

    def test_errors(self, app) -> None:
        """
        Validates the current input against numerical rules and defined
        bounds.

        Parameters
        ----------
        app : object
            The main application instance containing state and error_type
            attributes.

        """
        app.state = 'ERROR'
        if self.repre[0] == '':
            app.error_type = 'len0'
        elif np.sum(self.repre == '.') > 1:
            app.error_type = 'nan'
        elif self.repre[0] == '.':
            app.error_type = 'st.'
        elif len(self.repre) > self.bounds[1]:
            if (self.repre[0] == '0')&(self.repre[1] != '.'):
                app.error_type = '0n'
            elif float(self.temp) > self.bounds[1]:
                app.error_type = 'over'
            elif float(self.temp) < self.bounds[0]:
                app.error_type = 'under'
            else:
                app.state = 'IDLE'

        elif float(self.temp) > self.bounds[1]:
            app.error_type = 'over'
        elif float(self.temp) < self.bounds[0]:
            app.error_type = 'under'
        else:
            app.state = 'IDLE'

    def reloc_cursor(self) -> None:
        """
        Calculates and updates the visual position of the text cursor based on
        the current character widths and cursor index.
        """
        tot_len = []
        for c in self.repre:
            tx = self.font.render(c, 1, 'black')
            tot_len += [tx.get_width()]

        self.xy_cursor[0] = (self.center[0] - sum(tot_len) / 2 +
                             sum(tot_len[:self.cursor_idx]))

    def update_tx(self) -> None:
        """
        Synchronizes the internal string representation, re-renders the text
        surface, and updates centering positions.
        """
        self.reloc_cursor()
        if self.repre[0] == '':
            self.temp = ''
        else:
            self.temp = np.sum(self.repre)

        self.text_blit = self.font.render(self.temp, 1, 'black')
        self.text_blit_pos = [self.center[0]-self.text_blit.get_width()/2,
                              self.center[1]-self.text_blit.get_height()/2]

    def transform_event_key(self, event:pygame.event.Event) -> None:
        """
        Processes keyboard events to modify the button's text (inserting
        digits, handling backspace, or moving the cursor).

        Parameters
        ----------
        event : pygame.event.Event
            The keyboard event to be processed.

        """
        if ((event.unicode == '.')|(event.unicode.isdigit()))&(
            len(self.repre) < 15):

            if self.repre[0] != '':
                nw_len = len(self.repre)+1
                mask = np.ones(nw_len, dtype=bool)
                mask[self.cursor_idx] = False
                new_strings = np.array(['']*nw_len, dtype='<U2')
                new_strings[mask] = self.repre
                new_strings[self.cursor_idx] = event.unicode
                self.repre = new_strings.astype(object)
                self.cursor_idx += 1
                self.update_tx()

            else:
                self.repre = np.array([event.unicode], dtype=object)
                self.cursor_idx += 1
                self.update_tx()

        elif event.key == pygame.K_DELETE:
            if self.cursor_idx < len(self.repre):
                if len(self.repre) > 1:
                    mask = np.ones(len(self.repre), dtype=bool)
                    mask[self.cursor_idx] = False
                    self.repre = self.repre[mask]
                    self.update_tx()

                else:
                    self.repre = np.array([''], dtype=object)
                    self.cursor_idx = 0
                    self.update_tx()

        elif event.key == pygame.K_BACKSPACE:
            if self.cursor_idx > 0:
                if len(self.repre) > 1:
                    mask = np.ones(len(self.repre), dtype=bool)
                    mask[self.cursor_idx-1] = False
                    self.repre = self.repre[mask]
                    self.cursor_idx -= 1
                    self.update_tx()

                else:
                    self.repre = np.array([''], dtype=object)
                    self.cursor_idx = 0
                    self.update_tx()

        elif event.key == pygame.K_RIGHT:
            if self.cursor_idx < len(self.repre):
                self.cursor_idx += 1
                self.reloc_cursor()

        elif event.key == pygame.K_LEFT:
            if self.cursor_idx > 0:
                self.cursor_idx -= 1
                self.reloc_cursor()

        elif event.key == pygame.K_ESCAPE:
            self.sel_prop = False
        else:
            # other keys are not take into account
            pass

    def actions_click(self) -> None:
        """
        Handles mouse click logic to toggle the 'selected' state based on
        whether the mouse is hovering over the button.
        """
        if self.is_mouse_on:
            self.selected = not self.selected
        else:
            self.selected = False

    def actions_keyboard(self, event:pygame.event.Event) -> None:
        """
        Triggers text transformation logic if the button is currently
        selected.

        Parameters
        ----------
        event : pygame.event.Event
            The keyboard event to be passed to the transformer.

        """
        if self.selected:
            self.transform_event_key(event)

    def draw(self, window:pygame.surface.Surface) -> None:
        """
        Renders the button, text, and blinking cursor (if selected) to the
        screen.

        Parameters
        ----------
        window : pygame.surface.Surface
            The surface on which the button should be drawn.

        """
        pygame.draw.rect(window, 'white', self.draw_box)
        if self.is_mouse_on|self.selected:
            pygame.draw.rect(window, 'black', self.draw_box, self.lin_w)

        window.blit(self.text_blit, self.text_blit_pos)
        if self.selected&(time()%1 > 0.5):
            pygame.draw.line(window, 'black', (self.xy_cursor[0],
                self.xy_cursor[1]), (self.xy_cursor[0], self.xy_cursor[2]), 3)


class Inidication:
    """
    class to render color fields.

    Parameters
    ----------
    box : list
        Four values : x, y up-left corner position and width, height values.
    colors : list
        RGB color.

    """
    def __init__(self, box, color):
        self.box = box
        self.color = color

    def draw(self, window:pygame.surface.Surface) -> None:
        """
        Renders the fields.

        Parameters
        ----------
        window : pygame.surface.Surface
            Pygame surface object where buttons are draw.

        """
        pygame.draw.rect(window, self.color, self.box)


class Text:
    """
    Render text class.

    Parameters
    ----------
    x : int | float
        X axis center text position.
    y : int | float
        Y axis center text position.
    text : str
        Text to render.
    font : pygame.font.SysFont
        Font to use for rendering.

    """
    def __init__(self,
                 x:list,
                 y:list,
                 text:list,
                 font:pygame.font.SysFont) -> None:

        self.x = x
        self.y = y
        self.text = text
        self.font = font
        self.text_blit = []
        self.text_pos = []
        for i in range(len(self.x)):
            self.text_blit.append(self.font.render(self.text[i], 1, 'black'))
            self.text_pos.append([self.x[i]-self.text_blit[i].get_width()/2,
                                  self.y[i]-self.text_blit[i].get_height()/2])

    def draw(self, window:pygame.surface.Surface) -> None:
        """
        Renders the text.

        Parameters
        ----------
        window : pygame.surface.Surface
            Pygame surface object where buttons are draw.

        """
        for i in range(len(self.text)):
            window.blit(self.text_blit[i], self.text_pos[i])


import pygame
import numpy as np
from pathlib import Path
from unidecode import unidecode
from scipy.spatial.distance import cdist

# For string distances
import distances

# Object to manage the buttons
from database import DataGest

pygame.init()

class Matcher(DataGest):
    def __init__(self):
        super().__init__()

    def Levenshtein_rel_dist_es(self,
                                arr_str_1:np.ndarray,
                                arr_str_2:np.ndarray) -> float:
        """
        Levenshtein distance function with treshold based early stoping.

        Parameters
        ----------
        arr_str_1 : np.ndarray
            First array of the cleaned string from space and dot.
        arr_str_2 : np.ndarray
            Second array of the cleaned string from space and dot.

        Returns
        -------
        float
            Levenshtein relative distance with 1.0 when early stoping is
            triggered.

        """
        # self.treshold is a float (and not a np.float64)
        dist = distances.Levenshtein_rel_dist_es(arr_str_1, arr_str_2,
                                                 self.treshold)

        return dist

    def Levenshtein_abs_dist_es(self,
                                arr_str_1:np.ndarray,
                                arr_str_2:np.ndarray) -> float:
        """
        Levenshtein distance function with treshold based early stoping.

        Parameters
        ----------
        arr_str_1 : np.ndarray
            First array of the cleaned string from space and dot.
        arr_str_2 : np.ndarray
            Second array of the cleaned string from space and dot.

        Returns
        -------
        float
            Levenshtein absolute distance with 1.0 when early stoping is
            triggered.

        """
        # self.max_len is a float (and not a np.float64)
        dist = distances.Levenshtein_abs_dist_es(
            arr_str_1, arr_str_2, self.max_len)

        return dist

    def Damerau_Levenshtein_rel_dist_es(self,
                                        arr_str_1:np.ndarray,
                                        arr_str_2:np.ndarray) -> float:
        """
        Damerau-Levenshtein distance function with early stoping.

        Parameters
        ----------
        arr_str_1 : np.ndarray
            First cleaned string from space and dot.
        arr_str_2 : np.ndarray
            Secind cleaned string from space and dot.

        Returns
        -------
        float
            Damerau-Levenshtein relative distance with 1.0 if the early
            stoping is triggered.

        """
        dist = distances.Damerau_Levenshtein_rel_dist_es(
            arr_str_1, arr_str_2, self.treshold)

        return dist

    def Damerau_Levenshtein_abs_dist_es(self,
                                        arr_str_1:np.ndarray,
                                        arr_str_2:np.ndarray) -> float:
        """
        Damerau-Levenshtein distance function with early stoping.

        Parameters
        ----------
        arr_str_1 : np.ndarray
            First cleaned string from space and dot.
        arr_str_2 : np.ndarray
            Secind cleaned string from space and dot.

        Returns
        -------
        float
            Damerau-Levenshtein absolute distance with 1.0 if the early
            stoping is triggered.

        """
        dist = distances.Damerau_Levenshtein_abs_dist_es(
            arr_str_1, arr_str_2, self.max_len)

        return dist

    def preparations_rel_dists(self, mask_operations:np.ndarray,
                               mask_square:np.ndarray) -> np.ndarray:
        """
        Function to .

        Parameters
        ----------
        mask_operations : np.ndarray
            Vector, 1d boolean array.

        """
        # for Damerau-Levenshtein, I may need to implement a safer parameter
        # due to transposition matrix test for caracteres comparison
        if (self.to_compare == 'firstname'):
            prescore = np.minimum(
                self.auth_len_first[:, None], self.auth_len_first)/np.maximum(
                self.auth_len_first[:, None], self.auth_len_first)

            mask = prescore > self.treshold
            pre_d = cdist(self.bag_first, self.bag_first,
                          metric='cityblock') / 2 / np.maximum(
                self.auth_len_first[:, None], self.auth_len_first
                ) <= self.treshold

        elif (self.to_compare == 'lastname'):
            prescore = np.minimum(self.auth_len_last[:, None],
                self.auth_len_last) / np.maximum(
                self.auth_len_last[:, None], self.auth_len_last)

            mask = prescore > self.treshold
            pre_d = cdist(self.bag_last, self.bag_last,
                          metric='cityblock') / 2 / np.maximum(
                self.auth_len_last[:, None], self.auth_len_last
                ) <= self.treshold

        elif (self.to_compare == 'bothname'):
            prescore_f = np.minimum(self.auth_len_first[:, None],
                self.auth_len_first) / np.maximum(
                self.auth_len_first[:, None], self.auth_len_first)

            prescore_l = np.minimum(self.auth_len_last[:, None],
                self.auth_len_last) / np.maximum(
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
        return mask_operations

    def preparations_abs_dists(self, mask_operations:np.ndarray,
                               mask_square:np.ndarray) -> np.ndarray:
        """
        Function to .

        Parameters
        ----------
        mask_operations : np.ndarray
            Vector, 1d boolean array.

        """
        # for Damerau-Levenshtein, I may need to implement a safer parameter
        # due to transposition matrix test for caracteres comparison
        if (self.to_compare == 'firstname'):
            prescore = np.abs(
                self.auth_len_first[:, None]- self.auth_len_first)

            mask = prescore <= self.treshold
            pre_d = cdist(self.bag_first, self.bag_first,
                          metric='cityblock') / 2 <= self.treshold

        elif (self.to_compare == 'lastname'):
            prescore = np.abs(
                self.auth_len_last[:, None]-self.auth_len_last)

            mask = prescore <= self.treshold
            pre_d = cdist(self.bag_last, self.bag_last,
                          metric='cityblock') / 2 <= self.treshold

        elif (self.to_compare == 'bothname'):
            prescore_f = np.abs(
                self.auth_len_first[:, None]-self.auth_len_first)

            prescore_l = np.abs(
                self.auth_len_last[:, None]- self.auth_len_last)

            pre_f = cdist(self.bag_first,self.bag_first,metric='cityblock')/2
            pre_l = cdist(self.bag_last, self.bag_last, metric='cityblock')/2
            if self.both_comp == 'AND':
                mask = (prescore_f <= self.treshold)&(
                        prescore_l <= self.treshold)

                pre_d = (pre_f <= self.treshold)&(pre_l <= self.treshold)

            elif self.both_comp == 'OR':
                mask = (prescore_f <= self.treshold)|(
                        prescore_l <= self.treshold)

                pre_d = (pre_f <= self.treshold)|(pre_l <= self.treshold)

            elif self.both_comp == 'AVG':
                mask = ((prescore_f+prescore_l)/2) <= self.treshold
                pre_d = (pre_f + pre_l) / 2 <= self.treshold

        mask_operations = mask_operations & mask[mask_square]
        mask_operations = mask_operations & pre_d[mask_square]
        return mask_operations

    def preparation_matching(self) -> (np.ndarray, str, str, str, str):
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
        if self.to_filter in list(self.time_filter.keys()):
            mask_time = self.auth_time >= self.time_filter[self.to_filter]

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
            firstName_r = 'f_Name_r' ; lastName_r = 'l_Name_r'
        else:
            # First and Last names without special caracters,
            # removed with unicode.unicode
            firstName = 'firstName_uc' ; lastName = 'lastName_uc'
            firstName_r = 'f_Name_uc_r' ; lastName_r = 'l_Name_uc_r'

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

        elif self.to_compare == 'bothname':
            # Ignore the case if an author didn't give its first name (i.e.:
            # organisations, anonymous, some indonesian authors...)
            mask = (self.auth_len_last>0)&(self.auth_len_last[:, None]>0)
            mask_operations = mask_operations & mask[mask_square]
            mask = (self.auth_len_first>0)&(self.auth_len_first[:, None]>0)
            mask_operations = mask_operations & mask[mask_square]

        if self.algo in ['Levenshtein_rel', 'DamerauLevenshtein_rel']:
            mask_operations = self.preparations_rel_dists(
                mask_operations, mask_square)

        elif self.algo in ['Levenshtein_abs', 'DamerauLevenshtein_abs']:
            mask_operations = self.preparations_abs_dists(
                mask_operations, mask_square)

        # Re-Initialisation
        self.liste1 = [] ; self.liste2 = [] ; self.light = []

        self.initialize_bar(len(mask_operations))
        return mask_operations, firstName, lastName, firstName_r, lastName_r

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

        return not color

    def comparison_matching(self, app) -> None:
        """
        Function to compute the comparison between each authors pair.

        Parameters
        ----------
        app : Manager(DataGest)
            Manager class to get the other attributes.

        """
        # Global precomputing
        (mask_operations, firstName_rpr, lastName_rpr, firstName_cp,
         lastName_cp) = self.preparation_matching()

        if self.algo == 'Perfect':
            firstName_cp = firstName_rpr
            lastName_cp  = lastName_rpr
            is_match = lambda a, b: a == b

        else:
            if self.algo == 'Levenshtein_rel':
                # for optimisation use early stoping when treshold <= 0.78
                if self.treshold > 0.78:
                    f_dist = distances.Levenshtein_rel_dist
                else:
                    f_dist = self.Levenshtein_rel_dist_es

            elif self.algo == 'DamerauLevenshtein_rel':
                # for optimisation use early stoping when treshold <= 0.79
                if self.treshold > 0.79:
                    f_dist = distances.Damerau_Levenshtein_rel_dist
                else:
                    f_dist = self.Damerau_Levenshtein_rel_dist_es

            elif self.algo == 'Levenshtein_abs':
                # for optimisation use early stoping when treshold <= 1
                if self.treshold > 2:
                    f_dist = distances.Damerau_Levenshtein_abs_dist
                else:
                    f_dist = self.Damerau_Levenshtein_abs_dist_es

            elif self.algo == 'DamerauLevenshtein_abs':
                # for optimisation use early stoping when treshold <= 1
                if self.treshold > 2:
                    f_dist = distances.Damerau_Levenshtein_abs_dist
                else:
                    f_dist = self.Damerau_Levenshtein_abs_dist_es

            is_match = lambda a, b: f_dist(a, b) <= self.treshold

        color = False ; stop = False ; t = pygame.time.get_ticks()
        authkeys = np.sort(list(self.authors.keys()))
        num_aut = len(authkeys)
        app.draw()
        for i in range(num_aut-1):
            auth_1 = self.authors[authkeys[i]]
            for j in range(i+1, num_aut):
                auth_2 = self.authors[authkeys[j]]
                same = False
                if mask_operations[self.index]:
                    # Last / First name comparison
                    if self.to_compare == 'lastname':
                        if is_match(auth_1[lastName_cp], auth_2[lastName_cp]):
                            same = True
                            self.record_matching(
                                auth_1[lastName_rpr], auth_1[firstName_rpr],
                                auth_2[lastName_rpr], auth_2[firstName_rpr],
                                color)

                    elif self.to_compare == 'firstname':
                        if is_match(auth_1[firstName_cp],
                                    auth_2[firstName_cp]):
                            same = True
                            self.record_matching(
                                auth_1[firstName_rpr], auth_1[lastName_rpr],
                                auth_2[firstName_rpr], auth_2[lastName_rpr],
                                color)

                    elif self.to_compare == 'bothname':
                        d_l = f_dist(auth_1[lastName_cp], auth_2[lastName_cp])
                        d_f = f_dist(auth_1[firstName_cp],
                                     auth_2[firstName_cp])

                        if self.both_comp == 'AND':
                            # if one or two True == 1.0, else == 0.0
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
                                auth_1[lastName_rpr], auth_1[firstName_rpr],
                                auth_2[lastName_rpr], auth_2[firstName_rpr],
                                color)

                if same:
                    color = self.update_comparison(authkeys[i], authkeys[j],
                                                   color)

                self.index += 1
                if pygame.time.get_ticks() - t > self.refresh_rate:
                    t = pygame.time.get_ticks()
                    self.prog_box[2] = self.index * self.width_pb
                    app.draw()
                    stop = self.quit_in_loop(app)
                    if stop:
                        break

            if stop:
                break

        self.prog_bar = False

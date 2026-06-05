
import os
import json
import shutil
import pygame
import sqlite3
import numpy as np
import pandas as pd
import configparser
from pathlib import Path
from copy import deepcopy
from unidecode import unidecode
from scipy.spatial.distance import cdist

# For string distances
import distances

# Object to manage the buttons
from config import Config

pygame.init()

class DataGest(Config):
    def __init__(self):
        super().__init__()

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

        # Dynamic update of error message content
        self.error_messages['no file']['text'][3] = str(self.from_path)
        self.error_messages['no betbib']['text'][3] = str(self.from_path)
        self.to_path.mkdir(parents=True, exist_ok=True)
        if os.path.isfile(self.from_path / 'zotero.sqlite'):
            shutil.copyfile(self.from_path / 'zotero.sqlite',
                            self.to_path   / 'zotero.sqlite')

            if os.path.isfile(self.from_path / 'better-bibtex.sqlite'):
                self.use_zotero_db = False
                shutil.copyfile(self.from_path / 'better-bibtex.sqlite',
                                self.to_path   / 'better-bibtex.sqlite')

            elif os.path.isfile(self.from_path / 'better-bibtex.migrated'):
                self.use_zotero_db = False
                shutil.copyfile(self.from_path / 'better-bibtex.migrated',
                                self.to_path   / 'better-bibtex.migrated')

            else:
                # if no better-bibtex db found => will use zotero db
                # This behavior will be modified in the futur
                self.use_zotero_db = True

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

        Returns
        -------
        dico_tables : pd.DataFrame
            Data frame with the extracted data.

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
        if not self.use_zotero_db:
            # Extracts data from the Better BibTex database
            if os.path.isfile(self.to_path / 'better-bibtex.sqlite'):
                path_data = self.to_path / 'better-bibtex.sqlite'
            elif os.path.isfile(self.to_path / 'better-bibtex.migrated'):
                path_data = self.to_path / 'better-bibtex.migrated'
        
            self.data_cite_key = self.extract_valid_tables(path_data)
            self.data_cite_key = self.data_cite_key['citationkey'].loc[:,
                ['citationKey', 'itemID', 'itemKey']]

        else:
            key_field_id = int(self.data['fields'].loc[
                self.data['fields']['fieldName'] == 'citationKey',
                'fieldID'].values[0])

            self.data_cite_key = self.data['itemData'][
                self.data['itemData']['fieldID'] == key_field_id
                ].reset_index(drop=True)

            self.data_cite_key = self.data_cite_key.merge(
                self.data['itemDataValues'], on='valueID')

            self.data_cite_key = self.data_cite_key.merge(
                self.data['items'].loc[:, ['itemID', 'key']], on='itemID')

            self.data_cite_key = self.data_cite_key.rename(
                columns={'value':'citationKey', 'key':'itemKey'})

            self.data_cite_key = self.data_cite_key.drop(columns=['fieldID',
                                                                  'valueID'])

        self.one_loaded = True
        self.load_sq.color = [0, 200, 0]
        if self.comp_st == 2:
            self.comp_sq.color = [242, 133, 0]
            self.comp_st = 1

    def initialize_bar(self, max_ite:int) -> None:
        """
        Function to compute the parameters needed to render the progression
        bar.

        Parameters
        ----------
        max_ite : int
            Total number of iteration expected.

        """
        self.index = 0
        self.tot_idx = max_ite
        self.max_i_blit = self.TEXT_FONT.render(
            '/ '+str(self.tot_idx), 1, 'black')

        self.max_i_pos = (600*self.SCALE,
                          400*self.SCALE-self.max_i_blit.get_height()/2)

        self.idx_blit = self.TEXT_FONT.render(str(self.index), 1, 'black')
        self.idx_pos = [595*self.SCALE-self.idx_blit.get_width(),
                        400*self.SCALE-self.max_i_blit.get_height()/2]

        self.width_pb = (self.sp_pb - self.st_pb) / self.tot_idx
        self.prog_box[2] = 0
        self.prog_bar = True

    def treat_by_paper(self, app) -> None:
        """
        Function to extract usefull documents informations and pre compute
        some of ther caracteristics for optimisation.

        Parameters
        ----------
        app : Manager(DataGest)
            Manager class to get the other attributes.

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
        self.initialize_bar(self.num_elem)
        app.draw()
        stop = False ; t = pygame.time.get_ticks()
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

            self.index = i+1
            if pygame.time.get_ticks() - t > self.refresh_rate:
                t = pygame.time.get_ticks()
                self.prog_box[2] = self.index * self.width_pb
                app.draw()

                stop = self.quit_in_loop(app)
                if stop:
                    break

        if not stop:
            # 1d array for time comparison wich will be faster than loop
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
                self.auth_abv[i] = '.' in self.authors[authkeys[i]][
                                                                'firstName']

                l_red = self.reduce_string(
                    self.authors[authkeys[i]]['lastName'])

                f_red = self.reduce_string(
                    self.authors[authkeys[i]]['firstName'])

                self.authors[authkeys[i]]['l_Name_r'] = np.array(list(l_red))
                self.authors[authkeys[i]]['f_Name_r'] = np.array(list(f_red))
                self.authors[authkeys[i]]['l_Name_uc_r'] = np.array(list(
                                                            unidecode(l_red)))

                self.authors[authkeys[i]]['f_Name_uc_r'] = np.array(list(
                                                            unidecode(f_red)))

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
            self.prog_bar = False

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
            if self.to_filter in list(self.time_filter.keys()):
                mask_time = self.auth_time >= self.time_filter[self.to_filter]

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

    def quit_in_loop(self, app):
        """
        Function to be able to terminate the program without passing by
        comand killing process.

        Parameters
        ----------
        app : Manager(DataGest)
            Manager class to get the other attributes.

        Returns
        -------
        stop : bool
            If the loop con continue (False) or not (True).

        """
        stop = False
        for event in pygame.event.get():
            # Click handling (ignoring wheel as click)
            if event.type == pygame.QUIT:
                app.run = False
                stop = True
                break

        return stop

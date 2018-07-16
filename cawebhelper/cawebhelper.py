# -*- coding: utf-8 -*-
"""
Created on Tue May 30 09:21:13 2017

@author: renan.lisboa
"""
import re
import csv
import time
import pandas as pd
import unittest
import inspect
import socket
import sys
import os
from functools import reduce
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
import cawebhelper.enumerations as enum
from cawebhelper.log import Log
from cawebhelper.config import ConfigLoader
from cawebhelper.language import LanguagePack
from cawebhelper.third_party.xpath_soup import xpath_soup

class CAWebHelper(unittest.TestCase):
    def __init__(self, config_path=""):
        if config_path == "":
            config_path = sys.path[0] + r"\\config.json"
        self.config = ConfigLoader(config_path)
        if self.config.browser.lower() == "firefox":
            driver_path = os.path.join(os.path.dirname(__file__), r'drivers\\geckodriver.exe')
            log_path = os.path.join(os.path.dirname(__file__), r'geckodriver.log')
            self.driver = webdriver.Firefox(executable_path=driver_path, log_path=log_path)
        elif self.config.browser.lower() == "chrome":
            driver_path = os.path.join(os.path.dirname(__file__), r'drivers\\chromedriver.exe')
            self.driver = webdriver.Chrome(executable_path=driver_path)
        self.wait = WebDriverWait(self.driver,5)
        self.driver.maximize_window()
        self.driver.get(self.config.url)
        self.LastId = []
        self.LastIdBtn = []
        self.gridcpousr = []
        self.Table = []
        self.lenbutton = []
        self.idwizard = []

        self.grid_input = []
        self.grid_check = []
        self.date = ''
        self.rota = ''
        self.CpoNewLine = ''
        self.classe = ''
        self.valtype = ''
        self.cClass = ''
        self.savebtn = ''
        self.idcomp = ''
        self.rotina = ''
        self.lenvalorweb = ''
        self.IdClose = ''
        self.grid_value = ''
        self.grid_class = ''
        self.initial_program = 'SIGAADV'

        self.language = LanguagePack(self.config.language) if self.config.language else ""

        self.lineGrid = 0
        self.index = 0
        self.lastColweb = 0

        self.Ret = False
        self.refreshed = False
        self.consolelog = True
        self.btnenchoice = True
        self.elementDisabled = False
        self.numberOfTries = 0

        self.invalid_fields = []
        self.log = Log(console = self.consolelog)
        self.log.station = socket.gethostname()

        self.camposCache = []
        self.parametro = ''
        self.backupSetup = dict()


    def set_prog_inic(self, initial_program):
        '''
        Method that defines the program to be started
        '''
        if initial_program:
            self.initial_program = initial_program

        Id = self.SetScrap('inputStartProg', 'div', '')
        element = self.driver.find_element_by_id(Id)
        element.clear()
        self.SendKeys(element, self.initial_program)

    def set_enviroment(self):
        '''
        Method that defines the environment that will be used
        '''
        Id = self.SetScrap('inputEnv', 'div', '')
        element = self.driver.find_element_by_id(Id)
        element.clear()
        self.SendKeys(element, self.config.environment)


    def set_user(self):
        """
        Method that defines the environment that will be used
        """
        try:
            self.wait_element(term=self.language.user)
            Id = self.SetScrap(self.language.user, 'div', 'tget')
            if self.consolelog:
                print('SetUsr ID: %s' %Id)
            element = self.driver.find_element_by_id(Id)
            self.DoubleClick(element)
            self.SendKeys(element, Keys.HOME)
            self.SendKeys(element, self.config.user)

            resultado = self.get_web_value(Id).strip()
            if resultado != self.config.user:
                print('Conteúdo do campo usuário não preenchido. Buscando...')
                self.set_user()
            self.log.user = self.config.user
        except Exception as error:
            print(error)
            if self.consolelog:
                print("Não encontrou o campo Usuário")

    def set_password(self):
        """
        Complete the system password.
        """
        try:
            self.wait_element(term=self.language.user)
            Id = self.SetScrap(self.language.password, 'div', 'tget')
            if self.consolelog:
                print('SetUsr ID: %s' %Id)
            element = self.driver.find_element_by_id(Id)
            print('time.sleep(2) - 154')
            time.sleep(2)
            self.DoubleClick(element)
            self.SendKeys(element, Keys.HOME)
            self.SendKeys(element, self.config.password)
        except:
            if self.consolelog:
                print("Não encontrou o campo Senha")

    def set_based_date(self, trocaAmb):
        '''
        	Method that fills the date in the base date field.
        '''
        try:
            if trocaAmb:
                label = '%s*' %self.language.database
            else:
                label = self.language.database

            Id = self.SetScrap(label, 'div', 'tget')
            element = self.driver.find_element_by_id(Id)
            self.Click(element)
            self.SendKeys(element, Keys.HOME)
            self.SendKeys(element, self.config.date)
        except:
            if self.consolelog:
                print("Não encontrou o campo Database")

    def set_group(self, trocaAmb):
        '''
        Method that sets the group of companies in the system
        '''
        try:
            if trocaAmb:
                label = '%s*' %self.language.group
            else:
                label = self.language.group

            Id = self.SetScrap(label, 'div', 'tget')
            element = self.driver.find_element_by_id(Id)
            self.Click(element)
            self.SendKeys(element, self.config.group)
        except:
            if self.consolelog:
                print("Não encontrou o campo Grupo")

    def set_branch(self, trocaAmb):
        '''
        Method that fills the system branch
        '''
        try:
            if trocaAmb:
                label = '%s*' %self.language.branch
            else:
                label = self.language.branch

            Id = self.SetScrap(label, 'div', 'tget')
            self.idwizard.append(Id)
            element = self.driver.find_element_by_id(Id)
            self.Click(element)
            self.SendKeys(element, self.config.branch)
            self.SendKeys(element, Keys.TAB)
        except:
            if self.consolelog:
                print("Não encontrou o campo Filial")

    def set_module_of_system(self, trocaAmb):
        '''
        Method that fills the module used by the system
        '''
        try:
            if trocaAmb:
                label = '%s*' %self.language.environment
            else:
                label = self.language.environment

            Id = self.SetScrap(label, 'div', 'tget')
            element = self.driver.find_element_by_id(Id)
            self.Click(element)
            self.SendKeys(element, self.config.module)
        except:
            if self.consolelog:
                print("Não encontrou o campo Módulo")

    def SetItemMen(self, args1='', args2='', args3=''):
        '''
        Método que clica nos itens do menu
        '''
        Id = self.SetScrap(args1, 'li', 'tmenupopupitem', args3)
        if self.consolelog:
            print(Id + args1)
        if Id:
            if args1 and args2:
                ActionChains(self.driver).move_to_element(self.driver.find_element_by_xpath("//li[@id='%s']//label[.='%s']"%(Id, args1))).perform()
                Id = self.SetScrap(args2, 'li', 'tmenupopupitem', args3)
                if Id:
                    self.driver.find_element_by_xpath("//li[@id='%s']//label[.='%s']" %(Id, args2)).click()
            else:
                self.driver.find_element_by_xpath("//li[@id='%s']//label[.='%s']" %(Id, args1)).click()

    def wait_enchoice(self):
        Ret = ""
        if self.btnenchoice:
            self.btnenchoice = False
            while not Ret:
                Ret = self.element_exists(By.CSS_SELECTOR, "div.tbrowsebutton", text=self.language.cancel)
                if Ret:
                    self.cClass = 'tgetdados'
                else:
                    Ret = self.element_exists(By.CSS_SELECTOR, "div.tbrowsebutton", text=self.language.close)
                    if Ret:
                        self.cClass = 'tgrid'
            return Ret


    def wait_browse(self,searchMsg=True):
        Ret = ''
        endTime =   time.time() + 90
        while not Ret:
            Ret = self.SetScrap('fwskin_seekbar_ico.png', '', 'tpanel', 'indice')
            if time.time() > endTime:
                self.assertTrue(False, 'Tempo de espera para exibir os elementos do Browse excedido.')
        return Ret

    def SetRotina(self):
        '''
        Método que seta a rotina no campo pesquisa do menu
        '''

        Id = self.SetScrap('cGet', '', 'tget' )
        if Id:
            self.log.program = self.rotina
            element = self.driver.find_element_by_id(Id)
            self.DoubleClick(element)
            self.SendKeys(element, Keys.BACK_SPACE)
            self.SendKeys(element, self.rotina)
            element2 = self.driver.find_element_by_xpath("//div[@id='%s']/img" %Id)
            self.Click(element2)

        self.rota = 'SetRotina'

    def set_enchoice(self, campo='', valor='', cClass='', args='', visibility='', Id='', disabled=False, tries=100):
        '''
        Method that fills the enchoice.
        '''
        element = ""
        if tries == 10:
            self.numberOfTries = 0
            if self.elementDisabled and self.consolelog:
            	print("Element is Disabled")
            if not disabled:
                self.log_error(self.create_message(['', campo],enum.MessageType.DISABLED))
        else:
            tries += 1
            self.rota = "SetEnchoice"

            underline = (r'\w+(_)')#Se o campo conter "_"
            valsub = self.apply_mask(valor)

            if not Id:
                match = re.search(underline, campo)
                if match:
                    Id = self.SetScrap(campo, 'div', cClass, args)#Se for campo
                else:
                    Id = self.SetScrap(campo, 'div', cClass, args, 'label')#Se for Label

                if self.SearchStack('GetValue'):
                    return Id
            if Id:

                interface_value = self.get_web_value(Id)
                resultado = interface_value.strip()
                tam_interface = len(interface_value)
                if valsub != valor:
                    tam_valorusr = len(valsub)
                else:
                    tam_valorusr = len(valor)
                element = self.driver.find_element_by_id(Id)
                input_element = element.find_elements(By.TAG_NAME, 'input')
                if input_element:
                    element = input_element[0]

                self.scroll_to_element(element)#posiciona o scroll baseado na height do elemento a ser clicado.
                try:
                    if self.classe == 'tcombobox':
                        self.wait.until(EC.visibility_of(element))
                        self.set_selenium_focus(element)
                        self.select_combo(Id, valor)
                    else:
                        self.wait.until(EC.visibility_of(element))
                        self.wait.until(EC.element_to_be_clickable((By.ID, Id)))
                        self.DoubleClick(element)
                        if self.valtype != 'N':
                            self.SendKeys(element, Keys.DELETE)
                            self.SendKeys(element, Keys.HOME)

                        valsub = self.apply_mask(valor)

                        if valsub != valor and self.check_mask(element):
                            self.SendKeys(element, valsub)
                            valor = valsub
                        elif (self.valtype == "N"):
                            tries = 0
                            while(tries < 3):
                                self.set_selenium_focus(element)
                                self.SendKeys(element, Keys.DELETE)
                                self.SendKeys(element, Keys.BACK_SPACE)
                                self.Click(element)
                                element.send_keys(valor)
                                current_value = self.get_web_value(Id)
                                if self.apply_mask(current_value).strip() == valor:
                                    break
                                tries+=1
                        else:
                            self.SendKeys(element, valor)

                        if tam_valorusr < tam_interface:
                            self.SendKeys(element, Keys.ENTER)
                            # if self.valtype == 'N':
                            #     self.SendKeys(element, Keys.ENTER)
                            # else:
                           	# 	self.SendKeys(element, Keys.TAB)
                except Exception as error:
                    if self.consolelog:
                        print(error)
                    self.SetButton(self.language.cancel)
                    self.assertTrue(False, error)
                #print('time.sleep(1) - 385')
                #time.sleep(1)
                if self.check_mask(element):
                    resultado = self.apply_mask(self.get_web_value(Id).strip())[0:len(str(valor))]
                else:
                    resultado = self.get_web_value(Id).strip()[0:len(str(valor))]

                if self.consolelog and resultado != "":
                    print(resultado)

                if resultado.lower() != str(valor).strip().lower() and not re.match( r"^●+$", resultado ) and not self.valtype == 'N': #TODO AJUSTAR ESTE PONTO.
                    if self.elementDisabled:
                        self.numberOfTries += 1
                        self.set_enchoice(campo=campo, valor=valor, cClass='', args='', visibility='', Id=Id, disabled=disabled, tries=self.numberOfTries)
                    else:
                        if tries < 103:
                            self.set_enchoice(campo=campo, valor=valor, cClass='', args='', visibility='', Id=Id, disabled=disabled, tries=tries)
                        else:
                            self.log_error("Error trying to input value")

                elif re.match( r"^●+$", resultado ):
                    if len(resultado) != len(str(valor).strip()):#TODO AJUSTAR ESTE PONTO.
                        if tries < 103:
                            self.set_enchoice(campo=campo, valor=valor, cClass='', args='', visibility='', Id=Id, disabled=disabled, tries=tries)
                        else:
                            self.log_error("Error trying to input value")
    def select_combo(self, Id, valor):
        """
        Retorna a lista do combobox através do select do DOM.
        """
        combo = Select(self.driver.find_element_by_xpath("//div[@id='%s']/select" %Id))
        options = combo.options
        for x in options:
            if valor == x.text[0:len(valor)]:
                valor = x.text
                break
        if not self.elementDisabled:
            print('time.sleep(1) - 418')
            time.sleep(1)
            combo.select_by_visible_text(valor)
            print('time.sleep(1) - 421')
            time.sleep(1)
        return valor

    def SetGrid(self, ChkResult=0):
        """
        Preenche a grid baseado nas listas self.gridcpousr e self.Table
        """
        self.wait_enchoice() #Aguardo o carregamento dos componentes da enchoice.
        is_advpl = self.is_advpl()
        self.rota = "SetGrid"
        if self.fillTable():    # Se self.Table estiver preenchido com campos da tabela que o usuario quer testar, não deve executar SearchField() novamente.
            self.SearchField()  # Obtem a caracteristica dos campos da grid, gerando a lista self.Table

        td = ''
        self.lineGrid = 0
        for campo, valor, linha in self.gridcpousr:
            itens = lambda: self.driver.find_elements(By.CSS_SELECTOR, ".cell-mode .selected-row")
            for line in itens():
                if line.is_displayed():
                    td = line
                    break
            element = lambda: td.find_element(By.CSS_SELECTOR, ".selected-cell")
            self.lineGrid = int(td.get_attribute("id"))

            if not element():
                self.log_error("Celula não encontrada!")

            if campo == "newline" or (ChkResult and linha and ((linha - 1) != self.lineGrid)):
                self.lineGrid = int(td.get_attribute("id"))
                print('time.sleep(3) - 460')
                time.sleep(3)
                self.down_grid()
                print('time.sleep(3) - 463')
                time.sleep(3)
            else:
                coluna = self.Table[1].index(campo)
                if self.consolelog:
                    print('Posicionando no campo %s' %campo)
                # controla se a celula esta posicionada onde a variavel 'coluna' esta indicando e se a celula foi preenchida com o conteúdo da variavel 'valor'.
                while self.cawait(coluna, campo, valor, element, ChkResult):
                    Id = self.SetScrap('', 'div', self.cClass, 'setGrid')
                    if Id:
                        # nao estava posicionado na celula correta então tenta novamente e volta para a funcao cawait()
                        if is_advpl:
                            element_table = self.driver.find_element_by_xpath("//div[@id='%s']/div[1]/table/tbody/tr[@id=%s]/td[@id=%s]" % ( str(Id), str(self.lineGrid), str(coluna) ) )
                        else:
                            element_table = self.driver.find_element_by_xpath("//div[@id='%s']/div/table/tbody/tr[@id=%s]/td[@id=%s]/div" % ( str(Id), str(self.lineGrid), str(coluna) ) )
                        self.lastColweb = coluna
                        print('time.sleep(1) - 479')
                        time.sleep(1)
                        self.wait.until(EC.element_to_be_clickable((By.ID, Id)))
                        self.Click(element_table)
        # Neste momento devo limpar a lista gridcpousr, pois ja utilizei os seus dados.
        self.gridcpousr = []
        return True

    def SetTable(self):
        '''
        Método que retorna a table corrente
        '''
        # ADVPL
        #self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'tgetdados.twidget.dict-msbrgetdbase')))
        # MVC GRID NO FOLDER
        #self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "tgrid.twidget.dict-tgrid.CONTROL_ALIGN_ALLCLIENT.no-gridlines.cell-mode")))
        aux = []
        content = self.driver.page_source
        soup = BeautifulSoup(content,"html.parser")

        is_advpl = self.is_advpl()

        if is_advpl:
            # ADVPL
            grid = soup.find_all('div', class_=('tgetdados'))
            self.grid_class = ".tgetdados"
        else:
            # MVC GRID NO FOLDER
            grid = soup.find_all('div', class_=('tgrid'))
            self.grid_class = ".tgrid"
        #Seleção de filiis
        if not grid:
            grid = soup.find_all('div', class_=('tcbrowse'))
            self.grid_class = ".tcbrowse"

        if not is_advpl:
            for line in grid:
                if 'cell-mode' in line.attrs['class']:
                    aux += line
            grid = aux

        divstring = str(grid)
        soup = BeautifulSoup(divstring,"html.parser")
        rows = []
        xlabel = ''

        for tr in soup.find_all('tr'):

            cols = []
            for th_td in tr.find_all(['td', 'th']):
                th_td_text = th_td.get_text(strip=True)
                cols.append(th_td_text)
                xlabel = th_td.name

            if xlabel == 'td':
                rows[len(rows)-1][1].append(cols)
            else:
                rows.append([cols,[]])

        return rows

    def SetScrap(self, seek='', tag='', cClass='', args1='', args2='', args3=0, args4='', args5=60, searchMsg=True):
        '''
        Método responsável pelo retorno do ID utilizando WebScraping
        '''
        RetId = ''
        endTime =   time.time() + args5 #definição do timeout para 60 segundos
        refresh =   time.time() + 10 #definição do tempo para refresh da pagina inicial

        #Entra no loop somente se o RetId estiver vazio
        while not RetId:

            if args1 == 'Grid':
                if (self.Ret and args4 == 'SearchField') or (args3 == len(self.Table[0])):
                    break

            if not args1 == 'Grid':#Só espera 1 segundo se não for Grid
                print('time.sleep(0.5) - 547')
                time.sleep(0.5)#tempo de espera para cada verificação.
            if self.consolelog:
                print('Procurando %s' %seek)

            #Condições de retirada caso o timeout seja atingido
            if seek == 'inputStartProg':#se for a tela inicial e o tempo limite for atingido, faz o refresh da pagina.
                if time.time() > refresh and not self.refreshed:
                    if self.consolelog:
                        print('Refreshing...')
                    self.driver.refresh()
                    self.refreshed = True

            #faça somente se o tempo corrente for menor que o tempo definido no timeout
            if time.time() < endTime:
                content = self.driver.page_source
                soup = BeautifulSoup(content,"html.parser")

                #Verifica se possui errorlog na tela
                if searchMsg:
                    self.SearchErrorLog(soup)

                if not self.SearchStack('UTCheckResult') and searchMsg:
                    self.SearchHelp(soup)

                if seek == 'ChangeEnvironment':
                    RetId = self.caTrocaAmb(seek, soup, tag, cClass)
                    if RetId:
                        if self.consolelog:
                            print('caTrocaAmb')
                elif args1 == 'caHelp':
                    RetId = self.caHelp(seek, soup, tag, cClass)
                    if RetId:
                        if self.consolelog:
                            print('caHelp')
                    break
                elif args1 == 'caSeek':
                    RetId = self.caSeek(seek, soup, tag, cClass)
                    if RetId:
                        if self.consolelog:
                            print('caSeek')
                            break
                    break

                elif seek == 'language':
                    RetId = self.caLang(soup, tag, cClass)
                    if RetId:
                        break

                elif 'indice' in args1 or seek == 'placeHolder':
                    RetId = self.caSearch(seek, soup, 'div', cClass, args1, args2)
                    if self.consolelog:
                        print('caSearch')
                    if RetId:
                        break

                else:
                    RetId = self.cabutton(seek, soup, tag, cClass, args1, args2)
                    if RetId:
                        if self.consolelog:
                            print('cabutton')
                    if RetId == '':
                        RetId = self.camenu(seek, soup, tag, cClass, args1)
                        if RetId:
                            if self.consolelog:
                                print('camenu')

                    if RetId == '':
                        RetId = self.cainput(seek, soup, tag, cClass, args1, args2, args3, args4, args5)
                        if RetId:
                            if self.consolelog:
                                print('cainput')
            else:
                msg = ('O Campo ou Botão %s não foi encontrado' %seek)
                if self.consolelog:
                    print('TimeOut')
                if args1 == 'wait':
                    if self.consolelog:
                        print(args1)
                    break
                else:
                    self.assertTrue(False, msg)
                    break
        if RetId and self.consolelog:
            print("ID Retorno %s %s" %(seek, RetId))

        return(RetId)

    def cabutton(self, seek, soup, tag, cClass, args1, args2):
        '''
        identifica botoes
        '''
        lista = []
        RetId = ''
        # caso seja o botao 'Entrar', sera parseado por div + class
        if cClass == 'tbutton' and seek == self.language.enter:
            lista = soup.find_all('div', class_=('tbutton'))

        # entra somente quando botao Ok da chamada de parametros iniciais
        elif args1 == 'startParameters':
            RetId = soup.button.attrs['class'][0]

        elif cClass == 'tbrowsebutton':
            lista = soup.find_all(tag, class_=('tsbutton','tbutton', 'tbrowsebutton'))

        elif args1 == 'abaenchoice' :
            lista = soup.find_all(class_=(cClass))
            try:
                lista = lista[0].contents
            except:
                pass

        elif args1 == 'btnok':
            lista = soup.find_all(tag, class_=('tbutton', 'tsbutton', 'tbrowsebutton'))

        if not lista and not RetId:
            lista = soup.find_all(tag)

        lista = self.zindex_sort(lista,True)

        for line in lista:
            try:#faço uma tentativa pois caso não esteja verificando o mesmo nivel pode dar erro.
                if line.string:
                    text = line.string
                else:
                     text = line.text
                if (text[0:len(seek)] == seek) and (line.attrs['class'][0] == 'tbutton' or line.attrs['class'][0] == 'tbrowsebutton' or line.attrs['class'][0] == 'tsbutton') and line.attrs['id'] not in self.LastId and not args1 == 'setGrid':#TODO VERIFICAR SE TERÁ EFEITO USAR O LEN EM line.string
                    if self.savebtn == self.language.confirm and self.IdClose == line.attrs['id']:
	                    continue
                    RetId = line.attrs['id']
                    if self.savebtn:
                        if RetId not in self.lenbutton:
                            self.lenbutton.append(RetId)
                    if RetId not in self.LastIdBtn:
                        self.LastIdBtn.append(RetId)
                        RetId = self.LastIdBtn[len(self.LastIdBtn)-1]
                        if seek == self.language.other_actions:
                            if args1 == 'SearchBrowse':
                                self.teste = True
                        break
                '''
                if tooltipState == False and cClass == 'tbrowsebutton' and line.attrs['class'][0] == 'tbutton' and line.text == '':
                    tooltipId = self.SetButtonTooltip( seek, soup, tag, cClass )
                    if tooltipId == '':
                        tooltipState = False
                    else:
                        tooltipState = True

                if tooltipState == True and line.attrs['class'][0] == 'tbutton' and line.text == '':
                    if line.attrs['id'][4:8] == tooltipId:
                        RetId = line.attrs['id']
                        tooltipState = False
                        break
                '''
            except:
                pass

            #Somente se for aba da enchoice
            if args1 == 'abaenchoice':
                if seek == line.text:
                    RetId = line.attrs['id']
                    break

        return(RetId)

    def SetButtonTooltip(self, seek, soup, tag, cClass):
        '''
        Identifica o ID do Botão sem Rótulo/Texto.
        Via Tooltip ou via Nome da Imagem.
        '''
        tooltip = ''
        tooltipID = ''

        tooltipID = soup.find_all('div', text=seek)

        try: # Encontra o botão via nome da imagem
            if not tooltipID or tooltipID[1]:
                lista = soup.find_all(tag, class_=('tbutton'))
                menuItens = {self.language.copy: 's4wb005n.png',self.language.cut: 's4wb006n.png',self.language.paste: 's4wb007n.png',self.language.calculator: 's4wb008n.png',self.language.spool: 's4wb010n.png',self.language.help: 's4wb016n.png',self.language.exit: 'final.png',self.language.search: 's4wb011n.png', self.language.folders: 'folder5.png', self.language.generate_differential_file: 'relatorio.png',self.language.include: 'bmpincluir.png', self.language.visualizar: 'bmpvisual.png',self.language.editar: 'editable.png',self.language.delete: 'excluir.png',self.language.filter: 'filtro.png'}
                button = menuItens[seek]

                for line in lista:
                    if button in line.contents[1]['style']:
                        tooltip = line.attrs['id'][4:8]
                        break
        except: # Encontra o botão via Tooltip
            if tooltipID[0].text == seek:
                    tooltip = tooltipID[0].attrs['id'][8:12]

        return(tooltip)

    def cainput(self, seek, soup, tag, cClass, args1='', args2='', args3=0, args4='', args5=''):
        '''
        identifica input
        '''
        lista = []
        RetId = ''

        if seek == 'inputStartProg' or seek == 'inputEnv':
            lista = soup.find_all(id=seek)

        elif args1 == 'Grid':
            lista = soup.find_all(attrs={'name': re.compile(r'%s' %seek)})

        elif args1 == 'indice':
            if args2 == 'detail':
                lista = soup.find_all('div', class_=(cClass))
                if lista:
                    lista = lista[0].contents
            else:
                lista = soup.find_all('div', class_=(cClass))
            pass

        else:
            if args1 == 'Enchoice':
                #Tenta montar a lista por tag e que contenha classe
                lista = soup.find_all(tag, class_=True)

            else:
                if not lista:
                    lista = soup.find_all(tag, class_=(cClass))
                    if not lista:
                        #Tenta montar a lista somente por Tag
                        lista = soup.find_all(tag)

        for line in lista:
            #print('Passou uma vez %s' %time.time())
            # campo de input ex: Digitacao do Usuario
            try:
                if ((line.previous == seek or line.string == seek) and line.attrs['class'][0] == 'tget' and not args1 == 'Virtual' and not args2 == 'label' and line.attrs['class'][0] != 'tbrowsebutton') :
                    RetId = line.attrs['id']
                    self.classe = line.attrs['class'][0]
                    if not self.classe == 'tcombobox':
                        self.valtype = line.contents[0]['valuetype']
                    break

                elif seek == 'Inverte Selecao':
                    if seek == line.text:
                        RetId = line.attrs['id']
                        self.classe = line.attrs['class'][0]
                        if not self.classe == 'tcombobox':
                            self.valtype = line.contents[0]['valuetype']
                        break

                elif seek == 'cGet':
                    if line.attrs['name'] == 'cGet': #and line.next.attrs['class'][0] == 'placeHolder' and line.next.name == 'input':
                        RetId = line.attrs['id']
                        self.classe = line.attrs['class'][0]
                        if not self.classe == 'tcombobox':
                            self.valtype = line.contents[0]['valuetype']
                        self.LastId.append(RetId)
                        break

                elif seek == 'inputStartProg' or seek == 'inputEnv':
                    RetId = line.attrs['id']
                    self.classe = line.attrs['class'][0]
                    if not self.classe == 'tcombobox':
                        self.valtype = line.contents[0]['valuetype']
                    break

                elif seek == self.language.search:
                    if seek in line.previous and line.attrs['name'] == args1:
                        RetId = line.attrs['id']
                        self.classe = line.attrs['class'][0]
                        if not self.classe == 'tcombobox':
                            self.valtype = line.contents[0]['valuetype']
                        break

                elif args1 == 'Virtual':
                    if seek in line.text:
                        RetId = line.nextSibling.attrs['id']#Próximo Registro na mesma arvore de estrutura
                        break

                #Verifico se é a div correspondente a pasta ou tabela que foi passada pelo usuário.
                elif args1 == 'setGrid':
                    start = 0
                    end = 0
                    alllabels = []
                    for label in self.Table[0]:
                        start = end
                        end = start + len(label)
                        if line.text[start:end] == label:
                            alllabels.append(label)
                    if len(alllabels) == len(self.Table[0]):
                        RetId = line.attrs['id']
                        self.classe = line.attrs['class'][0]
                        if not self.classe == 'tcombobox':
                            self.valtype = line.contents[0]['valuetype']
                        break


                #Pesquisa o campo da enchoice/grid pelo nome do campo e retorna o ID equivalente.
                if args1 == 'Enchoice' or args1 == 'Grid':
                    if args1 == 'Grid':
                        if args4 == 'SearchField':
                            print('time.sleep(1) - 853')
                            time.sleep(1)
                            if seek in line.attrs['name']:
                                th = soup.find_all(class_=('selected-column'))

                                for i in th:
                                    if i.text == args2 and seek in line.attrs['name']:
                                        self.Table[2][args3] = line.attrs['name']
                                        self.Table[3][args3] = line.next.attrs['valuetype']
                        else:
                            pass
                    else:
                        if args2 == 'label':
                            if len(line.text.strip()) == len(seek.strip()):
                                if seek in line.text[0:len(seek)]:
                                    next_ = line.find_next_siblings('div')
                                    for x in next_:
                                        if x.attrs['class'][0] == 'tget' or x.attrs['class'][0] == 'tcombobox':
                                            if len(x.attrs['class']) > 3 and not self.SearchStack('UTCheckResult'):
                                                if x.attrs['class'][3] == 'disabled':
                                                    continue
                                            print(seek)

                                            #if cClass != '' and args2 != 'label' and args1 != 'Enchoice':
                                            Id = x.attrs['id']
                                            if Id not in self.idwizard:
                                                print(x.attrs['id'])
                                                self.idwizard.append(Id)
                                                self.classe = x.attrs['class'][0]
                                                RetId = Id
                                                if not self.classe == 'tcombobox':
                                                    self.valtype = x.contents[0]['valuetype']
                                                break
                                    if RetId:# IF/Break responsavel pela parada do FOR, quando é encontrado o ID do campo
                                        break
                                #preenche atributos do campo da enchoice
                        elif list(filter(bool, line.attrs["name"].split('->')))[1] == seek:
                            RetId = line.attrs['id']
                            self.classe = line.attrs['class'][0]
                            if not self.classe == 'tcombobox':
                                self.valtype = line.contents[0]['valuetype']
                            break
            except Exception: # Em caso de não encontrar passa para o proximo line
                pass
        #Se for uma chamada do método SearchField só busca uma unica vez
        if args4 == 'SearchField':
            self.Ret = True

        return(RetId)

    def seek_content(self, seek, contents, line=''):
        try:
            if not self.idcomp:
                if not contents:
                    #print(line)
                    if seek in str(line):
                        self.idcomp = line.parent.attrs['id']
                        return
                if len(contents) == 1:
                    if not contents[0].contents:
                        #print(str(contents[0]))
                        if seek in str(contents[0]):
                            self.idcomp = line.parent.attrs['id']
                            return
                    else:
                        for line in contents:
                            try:
                                self.seek_content(seek, line.contents, line)
                            except Exception:
                                pass
                    return
                else:
                    for line in contents:
                        try:
                            self.seek_content(seek, line.contents, line)
                        except Exception:
                            pass
                return
        except Exception:
            pass

    def camenu(self, seek, soup, tag, cClass, args1):
        '''
        identifica opcao do menu
        '''
        lista = []
        RetId = ''

        if cClass == 'tmenuitem':
            # monta a lista baseado na tag 'label' e na class 'tmenuitem'
            lista = soup.find_all('li', class_=('tmenuitem'))

        if cClass == '':
            RetId = ''

        else:
            lista = soup.find_all(tag, class_=(cClass))

        for line in lista:
            if seek in line.text and line.attrs['class'][0] == 'tmenuitem' and line.attrs['id'] not in self.LastId:
                RetId = line.attrs['id']
                self.LastId.append(RetId)
                break

            elif args1 == 'menuitem':
                if seek == line.text[0:len(seek)]:
                    RetId = line.attrs['id']
                    break

            else:
                if  self.savebtn == self.language.confirm and self.IdClose == line.attrs['id']:
	                continue
                if seek ==  line.text and not args1 == 'Virtual':
                    RetId = line.attrs['id']
                    break

        if len(lista) == 1 and cClass == "tmenu" and seek == "":
            RetId = lista[0].attrs['id']

        return(RetId)

    def caTrocaAmb(self, seek, soup, tag, cClass):
        lista = []
        RetId = ''
        lista = soup.find_all(tag, class_=(cClass))

        for line in lista:
            if line.text and len(line.attrs['class']) == 4 and line.attrs['class'][3] == 'CONTROL_ALIGN_RIGHT':
                RetId = line.attrs['id']
                if self.consolelog:
                    print(RetId)
                break
        return(RetId)

    def caSeek(self, seek, soup, tag, cClass):
        lista = []
        RetId = ''
        lista = soup.find_all(tag, class_=(cClass))

        for line in lista:
            if seek == line.attrs['name'][3:] and line.attrs['class'][0] == 'tcombobox':
                RetId = line.attrs['id']
                self.classe = line.attrs['class'][0]
                if self.consolelog:
                    print(RetId)
                break

            elif seek == line.attrs['name'][3:] and line.attrs['class'][0] == 'tget':
                RetId = line.attrs['id']
                self.classe = line.attrs['class'][0]
                if self.consolelog:
                    print(RetId)
                break
        return(RetId)

    def caHelp(self, seek, soup, tag, cClass):
        lista = []
        RetId = ''
        lista = soup.find_all(tag, class_=cClass)

        for line in lista:
            if seek in line.text:
                RetId = line.attrs['id']
                self.classe = line.attrs['class'][0]
                if self.consolelog:
                    print(RetId)
                break
        return(RetId)

    def caLang(self, soup, tag, cClass):
        lista = []
        lista = soup.find_all(tag, class_=(cClass))

        for line in lista:
            if line.attrs['lang']:
                language = line.attrs['lang']
                if self.consolelog:
                    print(language)
                break

        return(language)

    def caSearch(self, seek, soup, tag, cClass, args1, args2):
        """
        Método que busca o indice informado pelo usuário e efetua o preenchimento da chave no campo pesquisa do browse.
        """
        RetId = ''
        self.idcomp = ''
        element = ''
        Id = ''

        if args2 == 'detail':
            if args1 == 'indicedefault':
                #lista = self.search_next_soup(seek, soup)
                lista = soup.find_all("ul", class_=("tmenupopup"))
                for line in lista:
                    if "active" in line.attrs['class']:
                        if line.select(".tradiobutton"):
                            tradiobutton = line.find_all(class_='tradiobutton')
                            Id = tradiobutton[0].attrs['id']
                            break
            else:
                lista = soup.find_all('div', class_=(cClass))
                for line in lista:
                    if seek in line.text:
                        Id = line.attrs['id']
                        break
                if not Id:
                    self.log_error("Não foi encontrado o indice informado: {}".format(seek))
                    self.Restart()
        else:
            if args2:
                lista = self.search_next_soup(args2, soup)
            else:
                lista = soup.find_all('div', class_=(cClass))

            #Coleto o Id do campo pesquisa correspondente
            for line in lista:
                if cClass == 'tpanel':
                    if line.contents:
                        self.seek_content(seek, line.contents)
                        if self.idcomp:
                            RetId = self.idcomp
                            break

                #Busca o campo para preenchimento da chave de busca
                try:
                    if seek in line.contents[0].attrs['class'][0]:
                        RetId = line.attrs['id']
                        self.classe = line.attrs['class'][0]
                        self.LastIdBtn.append(RetId)
                        RetId = self.LastIdBtn[len(self.LastIdBtn)-1]
                except:
                    pass

            return(RetId)
        pass

        #Seleciona o botão correspondente a descrição do indice
        if cClass == 'tradiobutton':
            elem = self.driver.find_elements(By.ID, Id)
            radioitens = elem[0].find_elements(By.CLASS_NAME, 'tradiobuttonitem')
            if args1 == 'indicedefault':
                item = radioitens[0]
                if item.tag_name == 'div':
                    element = item.find_elements(By.TAG_NAME, 'input')[0]
                    self.DoubleClick(element)
                    RetId = True
            else:
                for item in radioitens:
                    if seek.strip() in item.text:
                        if item.tag_name == 'div':
                            element = item.find_elements(By.TAG_NAME, 'input')[0]
                            self.DoubleClick(element)
                            RetId = True
                            break
            return RetId

        #Busca pelo primeiro indice de busca
        elif seek == 'indicedefault':
            RetId = line.contents[0].attrs['id']

    def search_next_soup(self, seek, soup):
        """
        Retorna uma lista baseada no texto informado pelo usuário.
        """
        text = ''
        next_ = ''

        text = soup.find_all('div')

        for x in text:
            if seek == x.text:
                next_ = x.find_all_next('div')
                break
        return next_

    def get_zindex_position(self, list_, order=''):
        zindex = 0
        zindex_list = []

        for line in list_:
            zindex_content = line.attrs["style"].split("z-index:")[1].split(";")[0].strip()
            try:
                if zindex_content not  in zindex_list:
                    zindex_list.append(zindex_content)
                #zindex_list.append(int(line.attrs("style").split("z-index:")[1].split(";")[0].strip()))
            except:
                pass

        if order == 'ascending':
            zindex = sorted(zindex_list, key=int)
        elif order == 'descending':
            zindex = sorted(zindex_list, key=int, reverse=True)

        return zindex[0]

    def zindex_sort (self, elements, reverse=False):
        elements.sort(key=lambda x: self.search_zindex(x), reverse=reverse)
        return elements

    def search_zindex(self,element):
        zindex = 0
        if hasattr(element,"attrs") and "style" in element.attrs and "z-index:" in element.attrs['style']:
            zindex = int(element.attrs['style'].split("z-index:")[1].split(";")[0].strip())

        return zindex

    def SearchBrowse(self, chave, descricao=None, identificador=None):
        '''
        Mètodo que pesquisa o registro no browse com base no indice informado.
        '''
        self.wait_browse() #Verifica se já efetuou o fechamento da tela

        self.savebtn = ''
        # if self.rota == 'SetRotina' or self.rota == 'EDAPP':
        #     self.SetScrap(self.language.view, 'div', 'tbrowsebutton', 'wait', '', '', '', 10)
        #     self.rota = ''TODO VERIFICAR
        browse_elements = self.get_search_browse_elements(identificador)
        self.search_browse_key(descricao, browse_elements)
        self.fill_search_browse(chave, browse_elements)

    def get_search_browse_elements(self, panel_name=None):
        '''
        [Internal]
        [returns Tuple]
        Gets a tuple with the search browse elements in this order:
        Key Dropdown, Input, Icon.
        '''
        soup = self.get_current_DOM()
        search_index = self.get_panel_name_index(panel_name) if panel_name else 0
        containers = self.zindex_sort(soup.select(".tmodaldialog"), reverse=True)
        if containers:
            container = next(iter(containers))
            browse_div = container.select("[style*='fwskin_seekbar_ico']")[search_index].find_parent().find_parent()
            browse_tget = browse_div.select(".tget")[0]

            browse_key = browse_div.select(".tbutton button")[0]
            browse_input = browse_tget.select("input")[0]
            browse_icon = browse_tget.select("img")[0]

            return (browse_key, browse_input, browse_icon)

    def search_browse_key(self, key, search_elements):
        '''
        [Internal]
        Chooses the search key to be used during the search.
        '''
        sel_browse_key = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[0]))
        sel_browse_key().click()

        soup = self.get_current_DOM()
        tradiobuttonitens = soup.select(".tradiobuttonitem")
        tradio_index = 0

        if key:
            tradiobutton_texts = list(map(lambda x: x.text[0:-3].strip() if re.match(r"\.\.\.$", x.text) else x.text.strip(), tradiobuttonitens))
            tradiobutton_text = next(iter(list(filter(lambda x: x in key, tradiobutton_texts))))
            if tradiobutton_text:
                tradio_index = tradiobutton_texts.index(tradiobutton_text)

        tradiobuttonitem = tradiobuttonitens[tradio_index]
        sel_tradiobuttonitem = lambda: self.driver.find_element_by_xpath(xpath_soup(tradiobuttonitem))
        self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(tradiobuttonitem))))
        sel_tradiobuttonitem().click()


    def fill_search_browse(self, term, search_elements):
        '''
        [Internal]
        Fills search input method and presses the search button.
        '''
        sel_browse_input = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[1]))
        sel_browse_icon = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[2]))

        current_value = self.get_element_value(sel_browse_input())

        while (current_value.rstrip() != term.strip()):
            self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(search_elements[1]))))
            self.Click(sel_browse_input())
            sel_browse_input().clear()
            self.set_selenium_focus(sel_browse_input())
            sel_browse_input().send_keys(term.strip())
            current_value = self.get_element_value(sel_browse_input())
        self.SendKeys(sel_browse_input(), Keys.ENTER)

        self.DoubleClick(sel_browse_icon())
        return True

    def get_panel_name_index(self, panel_name):
        soup = self.get_current_DOM()
        panels = soup.select(".tmodaldialog > .tpanelcss > .tpanelcss")
        tsays = list(map(lambda x: x.select(".tsay"), panels))
        label = next(iter(list(filter(lambda x: x.text.lower() == panel_name.lower(), tsays)), None))
        return tsays.index(label)

    def wait_until_clickable(self, element):
        """
        Wait until element is clickable
        """
        endtime =   time.time() + 120# 2 minutos de espera

        if self.consolelog:
            print("Waiting...")
        while True:
            if time.time() < endtime:
                try:
                    element.click()
                    return True
                except:
                    pass
                    print('time.sleep(3) - 1230')
                    time.sleep(3)
            else:
                self.driver.save_screenshot( self.GetFunction() +".png")
                self.log_error("Falhou")

    # VISAO 3 - Tela inicial
    def ProgramaInicial(self, initial_program="", environment=""):
        self.set_prog_inic(initial_program)
        self.set_enviroment()
        button = self.driver.find_element(By.CSS_SELECTOR, ".button-ok")
        self.Click(button)

    def Usuario(self):
        """
        Preenchimento da tela de usuario
        """
        self.set_user()
        self.set_password()
        self.SetButton(self.language.enter, '', '', 60, 'button', 'tbutton')
        self.wait_element(term=self.language.user, scrap_type=enum.ScrapType.MIXED, presence=False, optional_term="input")

    def Ambiente(self, trocaAmb=False):
        """
        Preenche a tela de data base do sistema
        """
        self.set_based_date(trocaAmb)
        self.set_group(trocaAmb)
        self.set_branch(trocaAmb)
        self.set_module_of_system(trocaAmb)
        if trocaAmb:
            label = self.language.confirm
        else:
            label = self.language.enter

        self.SetButton(label,'','',60,'button','tbutton')
        self.wait_element(term=self.language.database, scrap_type=enum.ScrapType.MIXED, presence=False, optional_term="input")

    def Setup(self, initial_program, date='', group='99', branch='01', module=''):
        """
        Preenche as telas de programa inicial, usuario e ambiente.
        """
        #seta atributos do ambiente
        self.config.initialprog = initial_program
        self.config.date = date
        self.config.group = group
        self.config.branch = branch
        self.config.module = module

        if not self.config.valid_language:
            self.config.language = self.SetScrap("language", "html")
            self.language = LanguagePack(self.config.language)

        if not self.backupSetup:
            self.backupSetup = { 'progini': self.config.initialprog, 'data': self.config.date, 'grupo': self.config.group, 'filial': self.config.branch }
        if not self.config.skip_environment:
            self.ProgramaInicial(initial_program)

        self.Usuario()
        self.Ambiente()

        while(not self.element_exists(By.CSS_SELECTOR, ".tmenu")):
            self.close_modal()


        self.set_log_info()

    def Program(self, rotina):
        """
        Preenche a tela de rotina
        """
        self.rotina = rotina
        self.SetRotina()
        self.wait_browse() # Wait to load elements in browser

    def SetValue(self, campo, valor, grid=False, grid_number=1, disabled=False):
        """
        Indica os campos e o conteudo do campo para preenchimento da tela.
        """
        self.elementDisabled = False

        if not grid:
            if isinstance(valor,bool): # Tratamento para campos do tipo check e radio
                element = self.check_checkbox(campo,valor)
                if not element:
                   element = self.check_radio(campo,valor)
            else:
                self.wait_element(campo)
                self.set_enchoice(campo, valor, '', 'Enchoice', '', '', disabled)
        else:
            self.InputGrid(campo, valor, grid_number - 1)

    def LogOff(self):
        """
        Efetua logOff do sistema
        """
        Ret = self.wait_browse(False)
        if Ret:
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('q').key_up(Keys.CONTROL).perform()
            self.SetButton(self.language.finish,searchMsg=False)

    def TearDown(self):
        """
        Finaliza o browser
        """
        print('time.sleep(4) - 1354')
        time.sleep(4)
        self.driver.close()

    def VldData(self):
        """
        Decide qual caminho será seguido
        """
        if self.rota == 'SetValueItens' or self.rota == 'ClickFolder':
            if self.gridcpousr:
                self.SetGrid()
            self.rota = ''
        elif self.rota == 'CheckResultItens':
            # fim do caso de teste em segundos
            self.log.set_seconds()
            # indica ao SetGrid que haverá apenas conferencia de resultado.
            self.SetGrid(1)
            self.rota = ''
        return True

    def SearchField(self):
        """
        Obtem a caracteristica dos campos da grid, gerando a lista self.Table, essa lista sera
        utlizada para o preenchimento dos campos da grid.
        """
        try:
            regex = (r'\w+(_)')
            aux = ''
            alias = []
            field = []

            exceptions = ['wt alias', 'wt recno', 'alias wt', 'recno wt']
            lExcept = False
            auxTable = self.SetTable()
            self.Table = []

            #Separa somente o alias das tabelas sem repetir
            for line in self.gridcpousr:
                m = re.search(regex, line[0])
                if m:
                    aux = m.group()
                    if aux not in alias:
                        alias.append(aux)

            #Coleta so campos passado pelo usuário
            for line in self.gridcpousr:
                if line[0] not in field:
                    field.append(line[0])


            #caminho do arquivo csv(SX3)
            path = os.path.join(os.path.dirname(__file__), r'data\\sx3.csv')
            #DataFrame para filtrar somente os dados da tabela informada pelo usuário oriundo do csv.
            data = pd.read_csv(path, sep=';', encoding='latin-1', header=None, error_bad_lines=False,
                            index_col='Campo', names=['Campo', 'Tipo', 'Tamanho', 'Título', None], low_memory=False)
            df = pd.DataFrame(data, columns=['Campo', 'Tipo', 'Tamanho', 'Título', None])
            if not alias:
                df_filtered = df.query("Tipo=='C' or Tipo=='N' or Tipo=='D' ")
            else:
                df_filtered = df.filter(regex='^%s' %alias[0], axis=0)

            #Retiro os espaços em branco da coluna Campo e Titulo.
            df_filtered['Título'] = df_filtered['Título'].map(lambda x: x.strip())
            df_filtered.index = df_filtered.index.map(lambda x: x.strip())

            #Filtro somente os campos que foram passados pelo usuário
            #df_fields = df_filtered.loc[df_filtered.index.isin(field)]

            #Colunas do dataframe que serão utilizadas para alimentar o array de tabelas(self.Table)
            campo = df_filtered.index
            tipo = df_filtered['Tipo'].values
            Tamanho = df_filtered['Tamanho'].values
            #Verifico se a linha do vetor é correspondente à tabela do X3
            titulo = df_filtered['Título'].values

            acertos = []
            for index1, line in enumerate(auxTable):
                for line2 in line[0]:
                    if line2 in titulo:
                        acertos.append(line2)
                    else:
                        if alias:
                            for x in exceptions:
                                if line2.lower() == x:
                                    acertos.append(line2)
                                    lExcept = True
                                    break
                                else:
                                    lExcept = False
                            if not lExcept:
                                acertos = []
                                break


                if len(acertos) == len(line[0]):
                    self.Table.append(line[0])
                    self.index = index1
                    break

            tam = len(self.Table[0])
            self.Table.append( [''] * tam ) # sera gravado o nome dos campos da grid.
            self.Table.append( [''] * tam ) # sera gravado o tipo do campo, para ser utilizado na setgrid().
            self.Table.append( [''] * tam ) # será gravado o tamanho do campo.
            #self.Table.append( [''] * tam ) # posição do campo.
            lastindex = []
            for count in range(0, len(df_filtered)):
                if titulo[count].strip() in self.Table[0]:
                    index = self.Table[0].index(titulo[count].strip())#Busco a coluna titulo do dataframe na self.Table e utilizo como indice
                    if index not in lastindex:
                        self.Table[1][index] = campo[count].strip()
                        self.Table[2][index] = tipo[count]
                        self.Table[3][index] = Tamanho[count]
                        #self.Table[4][index] = index2
                        lastindex.append(index)
        except Exception as error:
            print("Entrou na exceção: %s" %error)

    def AddLine(self):
        """
        Inclui uma marca indicando nova linha, na lista gridcpousr.
        """
        if len(self.gridcpousr) > 0:
            self.gridcpousr.append(["newline", "", 0])

    def cawait(self, coluna, campo, valor, element, ChkResult):
        """
        Preenchimento e checagem dos campos da grid
        """
        try:
            # O scraping abaixo eh necessário para comparar se o que eu digitei no processo anterior, esta realmente preenchido na celula do grid.
            tipoCpo = self.Table[2][coluna]
            auxTable = self.SetTable()
            valorweb = auxTable[self.index][1][self.lineGrid][coluna]

            if self.SearchStack('GetValue'):
                self.grid_value = valorweb
                return False # return false encerra o laço

            valsub = self.apply_mask(valor)
            if self.lastColweb != coluna:
                return True
            else:
                # Esta sendo executado por UTCheckResult então apenas guardo o resultado
                if ChkResult:
                    self.LogResult(campo, valor, valorweb, True)
                else:
                    # O tipo do campo em que a celula esta posicionada eh 'Numerico' ?
                    if tipoCpo == 'N':
                        # O campo numérico esta vazio ?
                        if valorweb != valor:
                            # preencha o campo numerico
                            self.SendKeys(element(), Keys.ENTER)#element.send_keys(Keys.ENTER)
                            print('time.sleep(1) - 1506')
                            time.sleep(1)
                            self.SendKeys(element(), valsub)#element.send_keys(valor)
                            self.SendKeys(element(), Keys.ENTER)#element.send_keys(Keys.ENTER)

                            # return true fara com que entre novamente aqui( cawait ) para garantir que os dados foram preenchidos corretamente.
                            return True
                        else:
                            # o campo numerio foi preenchido corretamente, então o processo analisará o próximo campo contido em gridcpousr.
                            return False
                    # O tipo do campo em que a celula esta posicionada eh diferente de 'Numerico' !
                    # O conteudo da celula esta diferente da variavel 'valor'
                    elif valorweb != valor.strip():
                        #preencha campo
                        #clique enter na célula
                        #self.DoubleClick(element())#self.SendKeys(element, Keys.ENTER)
                        print('time.sleep(3) - 1522')
                        time.sleep(3)
                        self.enter_grid()
                        #Campo caractere
                        Id = self.SetScrap(campo,'div','tget', args1='caSeek')
                        #Se for combobox na grid
                        if not Id:
                            Id = self.SetScrap(campo,'div','tcombobox', args1='caSeek')
                            if Id:
                                valorcombo = self.select_combo(Id, valor)
                                if valorcombo[0:len(valor)] == valor:
                                    return False
                        if Id:
                            self.lenvalorweb = len(self.get_web_value(Id))
                            element_ = self.driver.find_element_by_id(Id)

                            if element_.tag_name == 'div':
                                element_ = element_.find_element_by_tag_name("input")

                            print('time.sleep(1) - 1541')
                            time.sleep(1)
                            self.Click(element_)
                            if valsub != valor and self.check_mask(element_):
                                self.SendKeys(element_, valsub)
                            else:
                                self.SendKeys(element_, valor)
                            if len(valor) < self.lenvalorweb:
                                self.SendKeys(element_, Keys.ENTER)
                        # return true fara com que entre novamente aqui( cawait ) para garantir que os dados foram preenchidos corretamente.
                        return True
                    else:
                        # o campo foi preenchido corretamente, então o processo analisará o próximo campo contido em gridcpousr.
                        return False
        except Exception as error:
            if self.consolelog:
                print(error)
            return True

    def CheckResult(self, cabitem, campo, valorusr, line=1, Id='', args1='', grid_number=1):
        """
        Validação de interface
        """
        # print('time.sleep(1) - 1554')
        # time.sleep(1)
        if args1 != 'input' and cabitem != 'help':
            self.wait_enchoice()
            self.rota = "UTCheckResult"
        valorweb = ''
        if not Id:
            if cabitem == 'aCab' and isinstance(valorusr,bool):
                valorweb = self.result_checkbox(campo,valorusr)
                self.LogResult(campo, valorusr, valorweb)
                return valorweb
            elif cabitem == 'aCab':
                underline = (r'\w+(_)')#Se o campo conter "_"
                match = re.search(underline, campo)
                if match:
                    Id = self.SetScrap(campo, 'div', 'tget', 'Enchoice')
                else:
                    Id = self.SetScrap(campo, 'div', 'tget', 'Enchoice', 'label')
            elif cabitem == 'Virtual':
                Id = self.SetScrap(campo, 'div', 'tsay', 'Virtual')
            elif cabitem == 'help':
                Id = self.SetScrap(valorusr, '','tsay twidget dict-tsay align-left transparent','caHelp')
        if cabitem != 'aItens':
            if Id:
                # print('time.sleep(1) - 1578')
                # time.sleep(1)
                element = self.driver.find_element_by_id(Id)
                if args1 != 'input':
                    self.Click(element)
                # print('time.sleep(1) - 1583')
                # time.sleep(1)
                valorweb = self.get_web_value(Id)
                self.lenvalorweb = len(valorweb)
                valorweb = valorweb.strip()
                if self.consolelog and valorweb != '':
                    print(valorweb)
                if self.check_mask(element):
                    valorweb = self.apply_mask(valorweb)
                    valorusr = self.apply_mask(valorusr)
                if type(valorweb) is str:
                    valorweb = valorweb[0:len(str(valorusr))]
                # print('time.sleep(1) - 1595')
                # time.sleep(1)
            if args1 != 'input':
                self.LogResult(campo, valorusr, valorweb)
        else:
            self.CheckGrid(line - 1, campo, valorusr, grid_number - 1)
            self.rota = 'CheckResultItens'
        if cabitem == 'help': # Efetua o fechamento da tela de help
            self.SetButton("Fechar")
            self.savebtn = ''

        return valorweb

    def get_web_value(self, Id):
        """
        Coleta as informações do campo baseado no ID
        """
        # quando o campo for combobox
        if self.classe == 'tcombobox':
            valorweb = self.driver.find_element_by_xpath("//div[@id='%s']/span" %Id).text
            if not valorweb:
                self.elementDisabled = self.driver.find_element_by_xpath("//div[@id='%s']/select" %Id).get_attribute('disabled') != None
        elif self.classe == 'tmultiget':
            valorweb = self.driver.find_element_by_xpath("//div[@id='%s']/textarea" %Id).get_attribute('value')
        elif self.classe == 'tsay':
            valorweb = self.driver.find_element_by_xpath("//div[@id='%s']/label" %Id).text
            if self.language.problem in valorweb:
                valorweb = valorweb.split('Problema: ')
                valorweb = valorweb[1]
        else:
            valorweb = self.driver.find_element_by_xpath("//div[@id='%s']/input" %Id).get_attribute('value')
            self.elementDisabled = self.driver.find_element_by_xpath("//div[@id='%s']/input" %Id).get_attribute('disabled') != None
        return valorweb

    def LogResult(self, field, user_value, captured_value, call_grid=False):
        '''
        Log the result of comparison between user value and captured value
        '''
        txtaux = ""
        message = ""
        if call_grid:
            txtaux = 'Item: %s - ' %str(self.lineGrid + 1)

        if user_value != captured_value:
            message = self.create_message([txtaux, field, user_value, captured_value], enum.MessageType.INCORRECT)

        self.validate_field(field, user_value, captured_value, message)

    def ChangeEnvironment(self):
        """
        clique na area de troca de ambiente do protheus
        """
        Id = self.SetScrap('ChangeEnvironment','div','tbutton')
        if Id:
            element = self.driver.find_element_by_id(Id)
            self.Click(element)
            self.Ambiente(True)

    def fillTable(self):
        """
        verifica se os dados de self.Table referem-se a tabela que o usuário vai testar.
        """
        retorno = 1 # sempre preencha a lista self.TableTable
        if len(self.Table):
            campo = self.gridcpousr[0][0]
            nseek = campo.find("_")
            arquivo = campo[:nseek]

            for linha in self.Table[1]:
                if arquivo in linha:
                    # não preencha a lista self.Table, pois, já foi preenchido em processos anteriores.
                    retorno = 0
                    break
        return retorno

    def AssertTrue(self):
        """
        Define que o teste espera uma resposta Verdadeira para passar
        """
        self.assert_result(True)

    def AssertFalse(self):
        """
        Define que o teste espera uma resposta Falsa para passar
        """
        self.assert_result(False)

    def Restart(self):
        self.LastIdBtn = []
        self.idwizard = []
        self.btnenchoice = True
        self.driver.refresh()
        self.driver.switch_to_alert().accept()
        if not self.config.skip_environment:
            self.ProgramaInicial()
        self.classe = ''
        self.Usuario()
        self.Ambiente()

        while(not self.element_exists(By.CSS_SELECTOR, ".tmenu")):
            self.close_modal()

        self.SetRotina()

    def GetFunction(self):
        stack = inspect.stack()
        function_name = "screenshot"
        for line in stack:
            if self.rotina in line.filename:
                return line.function
        return function_name

    def SearchStack(self,function):
        stack = inspect.stack()
        ret = False
        for line in stack:
            if line.function == function:
                ret = True
                break
        return ret

    def SearchErrorLog(self,soup):
        lista = soup.find_all('div', class_=('tsay twidget transparent dict-tsay align-left')) # Verifica de ocorreu error log antes de continuar
        if lista:
            for line in lista:
                if (line.string == self.language.messages.error_log):
                    self.SetButton(self.language.details,cClass='tbutton',searchMsg=False)
                    self.driver.save_screenshot( self.GetFunction() +".png")
                    self.log.new_line(False, self.language.messages.error_log_print)
                    self.log.save_file()
                    self.assertTrue(False, self.language.messages.error_log_print)

    def SearchHelp(self,soup):
        '''
        This method is called to treat Help messages
        '''
        lista = soup.find_all('div', class_=('workspace-container')) # Leva como base div inicial
        if lista:
            lista = lista[0].contents # Pega filhos da tela principal
            for line in lista:
                message = ""
                if line.text == self.language.messages.error_msg_required:
                    message = self.language.messages.error_msg_required
                    self.search_help_error(message)
                elif self.language.help in line.text and self.language.problem in line.text:
                    message = line.text
                    self.search_help_error(message)

    def search_help_error(self, message):
        '''
        This method is part of SearchHelp internal functionality
        '''
        is_advpl = self.is_advpl()

        self.driver.save_screenshot( self.GetFunction() +".png")
        self.SetButton(self.language.close,cClass='tbutton',searchMsg=False)
        self.savebtn = ''

        close_element = self.get_closing_button(is_advpl)

        self.Click(close_element)
        if not is_advpl:
            self.SetButton(self.language.leave_page,cClass='tbutton',searchMsg=False)
        self.log.new_line(False, message)
        self.log.save_file()
        self.assertTrue(False, message)

    def Click(self, element):
        try:
            self.scroll_to_element(element)
            element.click()
        except Exception:
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            self.scroll_to_element(element)
            actions.click()
            actions.perform()

    def move_element(self, element):
        actions = ActionChains(self.driver)
        actions.move_to_element(element)
        actions.perform()

    def DoubleClick(self, element):
        try:
            self.scroll_to_element(element)
            element.click()
            element.click()
        except Exception:
            self.scroll_to_element(element)
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            actions.double_click()
            actions.perform()

    def SendKeys(self, element, args):
        try:
            element.send_keys("")
            element.click()
            element.send_keys(args)
        except Exception:
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            actions.send_keys("")
            actions.click()
            actions.send_keys(args)
            actions.perform()

    def create_message(self, args, messageType=enum.MessageType.CORRECT):
        '''
        Returns default messages used all throughout the class.
        '''
        correctMessage = "{} Valor fornecido para o campo {} esta correto!"
        incorrectMessage = "{} Valor fornecido para o campo \"{}\" ({}) não confere com o valor encontrado na interface ({})."
        disabledMessage = "{} Campo \"{}\" esta desabilitado."
        assertErrorMessage = "Falhou: Valor fornecido para o campo {}: \"{}\" não confere com o valor encontrado na interface \"{}\"."

        if messageType == enum.MessageType.INCORRECT:
            return incorrectMessage.format(args[0], args[1], args[2], args[3])
        elif messageType == enum.MessageType.DISABLED:
            return disabledMessage.format(args[0], args[1])
        elif messageType == enum.MessageType.ASSERTERROR:
            return assertErrorMessage.format(args[0], args[1], args[2])
        else:
            return correctMessage.format(args[0], args[1])

    def element_exists(self, by, selector, position=None,text=''):
        '''
        Returns a boolean if element exists on the screen
        '''
        if self.consolelog:
            print(f"By={by}, selector={selector}, position={position}, text={text}")
        if position is None and not text:
            element_list = self.driver.find_elements(by, selector)
            return len(element_list) > 0
        elif position is not None and not text:
            element_list = self.driver.find_elements(by, selector)
            return len(element_list) >= position
        else:
            print('time.sleep(1) - 1840')
            time.sleep(1)

            content = self.driver.page_source
            soup = BeautifulSoup(content,"html.parser")

            elements = list(soup.select(selector))

            for element in elements:
                if text in element.text:
                    return True
            return False

    def SetLateralMenu(self, menuitens):
        '''
        Navigates through the lateral menu using provided menu path.
        e.g. "MenuItem1 > MenuItem2 > MenuItem3"
        '''
        self.wait_element(term=".tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR)
        menuitens = list(map(str.strip, menuitens.split(">")))

        menuId = self.SetScrap(cClass="tmenu")
        menu = lambda: self.driver.find_element_by_id(menuId)

        for menuitem in menuitens:
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".tmenu")))
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tmenu .tmenuitem")))
            self.wait_element(term=menuitem, scrap_type=enum.ScrapType.MIXED, optional_term=".tmenuitem")
            subMenuElements = menu().find_elements(By.CSS_SELECTOR, ".tmenuitem")
            submenu = ""
            for child in subMenuElements:
                if child.text.startswith(menuitem):
                    submenu = child
                    break
            if subMenuElements and submenu:
                self.scroll_to_element(submenu)
                self.Click(submenu)
                menu = lambda: submenu
            else:
                response = "Error - Menu Item does not exist: {}".format(menuitem)
                print(response) #Send to Better Log
                self.assertTrue(False, response)


    def scroll_to_element(self, element):
        '''
        Scroll to element on the screen.
        '''
        if element.get_attribute("id"):
            self.driver.execute_script("return document.getElementById('{}').scrollIntoView();".format(element.get_attribute("id")))
        else:
            self.driver.execute_script("return arguments[0].scrollIntoView();", element)

    def GetValue(self, cabitem, field):
        '''
        Get a web value from DOM elements
        '''
        value = ''

        if cabitem == 'aCab':
            Id = self.set_enchoice(campo=field, args='Enchoice')
            value = self.get_web_value(Id)
        elif cabitem == 'aItens':
            self.gridcpousr.append([field, '', 0])
            self.SetGrid()
            if self.grid_value:
                value = self.grid_value
                self.grid_value = ''


        return value

    def validate_field(self, field, user_value, captured_value, message):
        '''
        Validates and stores field in the self.invalid_fields array if the values are different.
        '''
        if str(user_value).strip() != str(captured_value).strip():
            self.invalid_fields.append(message)

    def assert_result(self, expected):
        expected_assert = expected
        msg = "Passed"
        stack = list(map(lambda x: x.function, filter(lambda x: re.search('test_', x.function),inspect.stack())))[0]
        stack = stack.split("_")[-1]
        log_message = ""
        log_message += stack + " - "

        if self.invalid_fields:
            expected = not expected

            for field_msg in self.invalid_fields:
                log_message += (" " + field_msg)

            msg = log_message

            self.log.new_line(False, log_message)
        else:
            self.log.new_line(True, "")

        self.log.save_file()

        self.invalid_fields = []
        print(msg)
        if expected_assert:
            self.assertTrue(expected, msg)
        else:
            self.assertFalse(expected, msg)

    def set_log_info(self):
        self.log.initial_time = time.time()
        self.SetLateralMenu(self.language.menu_about)
        self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tmodaldialog")))

        content = self.driver.page_source
        soup = BeautifulSoup(content,"html.parser")

        modal = list(soup.select(".tmodaldialog")[0].children)

        for panel in modal:
            for element in panel.children:
                if element.text.startswith("Release"):
                    release = element.text.split(":")[1].strip()
                    self.log.release = release
                    self.log.version = release.split(".")[0]
                elif element.text.startswith("Top DataBase"):
                    self.log.database = element.text.split(":")[1].strip()
                else:
                    if self.log.version and self.log.release and self.log.database:
                        break

        self.SetButton(self.language.close)

    def SetButton(self, button, args1='wait', args2='', args3=45, tag='div', cClass='tbrowsebutton',searchMsg = True):
        '''
        Method that clicks on a button of the interface.
        '''
        try:
            Id  = ''
            if (button.lower() == "x"):
                self.wait_element(term=".ui-button.ui-dialog-titlebar-close[title='Close']", scrap_type=enum.ScrapType.CSS_SELECTOR)
            else:
                self.wait_element_timeout(button, timeout=2.5, step=0.5)

            layers = 0
            if button == self.language.confirm:
                layers = len(self.driver.find_elements(By.CSS_SELECTOR, ".tmodaldialog"))

            if self.VldData():

                success = False
                if (button.lower() == self.language.Ok.lower()) and args1 != 'startParameters':
                    Id = self.SetScrap(button, tag, '', 'btnok')
                elif (button.lower() == "x" and self.element_exists(By.CSS_SELECTOR, ".ui-button.ui-dialog-titlebar-close[title='Close']")):
                    element = self.driver.find_element(By.CSS_SELECTOR, ".ui-button.ui-dialog-titlebar-close[title='Close']")
                    self.scroll_to_element(element)
                    time.sleep(2)
                    self.Click(element)
                elif button in self.language.no_actions:
                    Id = self.SetScrap(button, tag, cClass, '', '', '', '', 60, searchMsg)
                elif button != self.language.other_actions:
                    Id = self.SetScrap(button, tag, cClass, args1, '', '', '', args3, searchMsg)
                if not Id:
                    other_actions = self.SetScrap(self.language.other_actions, tag, cClass, args1,'', '', '', args3,searchMsg)
                    other_actions_element = self.driver.find_element_by_id(other_actions)
                    self.Click(other_actions_element)
                    success = self.click_sub_menu(button if button.lower() != self.language.other_actions.lower() else args1)
                    if success:
                        return
                if Id:
                    if button == self.language.confirm or button == self.language.save:
                        self.savebtn = button
                    if Id == 'button-ok':
                        element = self.driver.find_element_by_class_name(Id)
                    else:
                        element = self.driver.find_element_by_id(Id)

                    time.sleep(3)
                    self.scroll_to_element(element)#posiciona o scroll baseado na height do elemento a ser clicado.
                    self.Click(element)

                    if button == self.language.add:
                        if args1 != '' and args1 != 'wait':#se for botão incluir com subitens
                            Id = self.SetScrap(args1, 'li', 'tmenupopupitem')
                            if Id:
                                element = self.driver.find_element_by_id(Id)
                                self.Click(element)

            if button == self.language.confirm and Id in self.get_enchoice_button_ids(layers):
                self.wait_element(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=layers + 1)

            if button == self.language.edit or button == self.language.view or button == self.language.delete or button == self.language.add:
                if not self.element_exists(By.CSS_SELECTOR, ".ui-dialog"):
                    #self.wait_enchoice()
                    self.btnenchoice = True

        except ValueError as error:
            if self.consolelog:
                print(error)
            self.log_error("Campo %s não encontrado" %error.args[0])
        except Exception as error:
            if self.consolelog:
                print(error)
            self.log_error(str(error))

    def click_sub_menu(self, button):
        '''
        Método que clica nos itens do menu
        '''
        content = self.driver.page_source
        soup = BeautifulSoup(content,"html.parser")

        menu_id = self.zindex_sort(soup.select(".tmenupopup.active"), True)[0].attrs["id"]
        menu = self.driver.find_element_by_id(menu_id)

        menu_itens = menu.find_elements(By.CSS_SELECTOR, ".tmenupopupitem")

        result = self.find_sub_menu_text(button, menu_itens)

        item = ""
        if result[0]:
            item = result[0]
        elif result[1]:
            item = self.find_sub_menu_child(button, result[1])
        else:
            return False

        if item:
            self.scroll_to_element(item)
            self.Click(item)
            return True
        else:
            return False

    def find_sub_menu_child(self, button, containers):
        item = ""
        for child in containers:

            child_id = child.get_attribute("id")
            old_class = self.driver.execute_script("return document.querySelector('#{}').className".format(child_id))
            new_class = old_class + " highlighted expanded"
            self.driver.execute_script("document.querySelector('#{}').className = '{}'".format(child_id, new_class))

            child_itens = child.find_elements(By.CSS_SELECTOR, ".tmenupopupitem")
            result = self.find_sub_menu_text(button, child_itens)

            if not result[0] and result[1]:
                item = self.find_sub_menu_child(button, result[1])
            else:
                item = result[0]
                if item:
                    break
                self.driver.execute_script("document.querySelector('#{}').className = '{}'".format(child_id, old_class))

        return item

    def find_sub_menu_text(self, button, itens):
        submenu = ""
        containers = []
        for child in itens:
            if "container" in child.get_attribute("class"):
                containers.append(child)
            elif child.text.startswith(button):
                submenu = child
                break

        return (submenu, containers)

    def SetBranch(self, branch):
        """
        Método que preenche a filial na inclusão
        """
        self.wait_element(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR, position=2)
        Ret = self.fill_search_browse(branch, self.get_search_browse_elements())
        if Ret:
            self.SetButton('OK','','',60,'div','tbutton')
            #self.wait_enchoice()

    def WaitWhile(self,itens):
        '''
        Search string that was sent and wait while condition is true
        e.g. "Item1,Item2,Item3"
        '''
        self.search_text(itens,True)

    def WaitUntil(self,itens):
        '''
        Search string that was sent and wait until condition is true
        e.g. "Item1,Item2,Item3"
        '''
        self.search_text(itens,False)

    def search_text(self,itens,invert):
        '''
        Search string that was sent and wait until condition is respected
        e.g. "Item1,Item2,Item3"
        '''
        itens = list(map(str.strip, itens.split(",")))
        print("Aguardando processamento...")
        while True:
            content = self.driver.page_source
            soup = BeautifulSoup(content,"html.parser")
            lista = soup.find_all('div', string=(itens))
            if invert:
                if not lista:
                    break
            else:
                if lista:
                    break
            print('time.sleep(5) - 2081')
            time.sleep(5)

    def SetTabEDAPP(self, tabela):
        '''
        Method that fills the field with the table to be checked in the generic query
        '''
        try:
            Id = self.SetScrap(self.language.search, 'div', 'tget', 'cPesq')
            element = self.driver.find_element_by_id(Id)
            self.Click(element)
            self.SendKeys(element, tabela)
            self.SendKeys(element, Keys.ENTER)
            self.SetButton('Ok','','',60,'div','tsbutton')
        except:
            if self.consolelog:
                print("Não encontrou o campo Pesquisar")
        self.rota = 'EDAPP'

    def ClickFolder(self, item):
        '''
        Método que efetua o clique na aba
        '''
        self.rota = "ClickFolder"

        if self.VldData():
            self.wait_element(term=item, scrap_type=enum.ScrapType.MIXED, optional_term=".button-bar a")
            #Retira o ToolTip dos elementos focados.
            self.move_element(self.driver.find_element_by_tag_name("html"))

            #try:#Tento pegar o elemento da aba de forma direta sem webscraping
            #    element = lambda: self.driver.find_element_by_link_text(item)
            #except:#caso contrário efetuo o clique na aba com webscraping
            soup = self.get_current_DOM()
            panels = soup.select(".button-bar a")
            panel = next(iter(list(filter(lambda x: x.text == item, panels))))
            element = ""
            if panel:
                element = lambda: self.driver.find_element_by_xpath(xpath_soup(panel))
            if element:
                self.scroll_to_element(element())#posiciona o scroll baseado na height do elemento a ser clicado.
                self.set_selenium_focus(element())
                time.sleep(1)
                self.driver.execute_script("arguments[0].click()", element())
            else:
                self.log_error("Couldn't find panel item.")

    def ClickBox(self, fields, contents_list, browse_index=1 ):
        '''
        Method that clicks in checkbox
        '''

        soup = self.get_current_DOM()

        grids = soup.find_all('div', class_=(['tgetdados','tgrid','tcbrowse']))

        if grids:
            if len(grids) > 1:
                grids = self.filter_displayed_elements(grids,False)
            else:
                grids = self.filter_displayed_elements(grids,True)

            self.current_tables = grids

        contents_list = contents_list.split(",")
        fields = fields.split(",")
        browse_index -= 1

        if contents_list == 'Todos':
            self.wait_element('Inverte Selecao') # wait Inverte Seleção
            Id = self.SetScrap('Inverte Selecao', 'label', 'tcheckbox')
            if Id:
                element = self.driver.find_element_by_id(Id)
                self.Click(element)
        else:
            for line in fields:
                self.wait_element(line) # wait columns
                break

            for line in contents_list:
                self.wait_element(line) # wait columns
                break

            table_structs = self.SetTable()
            table_struct = table_structs[browse_index] # Pega o browse valido na tela
            grid = self.current_tables[browse_index]

            class_grid = grid.attrs['class'][0]
            grid = self.driver.find_element_by_xpath(xpath_soup(grid))

            for line in contents_list:
                for x in range(0, len(table_struct)):
                    for index, y in enumerate(table_struct[x][1]):
                        if line.strip() == y[1]:
                            elements_list = grid.find_elements(By.CSS_SELECTOR, "td[id='1']")
                            self.scroll_to_element(elements_list[index])
                            self.Click(elements_list[index])
                            if class_grid != 'tcbrowse':
                                print('time.sleep(1)')
                                time.sleep(1)
                                self.DoubleClick(elements_list[index])
                                print('time.sleep(2)')
                                time.sleep(1)
                            else:
                                self.SendKeys(elements_list[index], Keys.ENTER)
                            break
        self.current_tables = ''

    def SetParameters( self, arrayParameters ):
        '''
        Método responsável por alterar os parâmetros do configurador antes de iniciar um caso de teste.
        '''
        self.idwizard = []
        self.LogOff()

        #self.Setup("SIGACFG", "10/08/2017", "T1", "D MG 01")
        self.Setup("SIGACFG", self.config.date, self.config.group, self.config.branch)

        # Escolhe a opção do Menu Lateral
        self.SetLateralMenu("Ambiente > Cadastros > Parâmetros")

        # Clica no botão/icone pesquisar
        self.SetButton("Pesquisar")

        array = arrayParameters

        backup_idwizard = self.idwizard[:]

        for arrayLine in array:

            # Preenche o campo de Pesquisa
            self.SetValue("aCab", "Procurar por:", arrayLine[0])

            # Confirma a busca
            self.SetButton("Buscar")

            # Clica no botão/icone Editar
            self.SetButton("Editar")

            # Faz a captura dos elementos dos campos
            print('time.sleep(5) - 2204')
            time.sleep(5)
            content = self.driver.page_source
            soup = BeautifulSoup(content,"html.parser")

            menuCampos = { 'Procurar por:': arrayLine[0], 'Filial': '', 'Cont. Por': '', 'Cont. Ing':'', 'Cont. Esp':'' }

            for line in menuCampos:
                if not menuCampos[line]:
                    RetId = self.cainput( line, soup, 'div', '', 'Enchoice', 'label', 0, '', 60 )
                    cache = self.get_web_value(RetId)
                    self.lencache = len(cache)
                    cache = cache.strip()
                    menuCampos[line] = cache

            self.camposCache.append( menuCampos )
            self.idwizard = backup_idwizard[:]

            # Altero os parametros
            self.SetValue("aCab", "Filial", arrayLine[1])
            self.SetValue("aCab", "Cont. Por", arrayLine[2])
            self.SetValue("aCab", "Cont. Ing", arrayLine[3])
            self.SetValue("aCab", "Cont. Esp", arrayLine[4])

            # Confirma a gravação de Edição
            self.SetButton("Salvar")
            self.idwizard = backup_idwizard[:]
        self.LogOff()

        self.Setup( self.backupSetup['progini'], self.backupSetup['data'], self.backupSetup['grupo'], self.backupSetup['filial'])
        self.Program(self.rotina)

    def RestoreParameters( self ):
        '''
        Método responsável por restaurar os parâmetros do configurador após o encerramento do/dos caso(s) de teste(s).
        Método deve ser executado quando for alterado os parametros do configurador, utilizando o método SetParameters()
        '''
        self.idwizard = []
        self.LogOff()

        self.Setup("SIGACFG", "10/08/2017", "T1", "D MG 01")

        # Escolhe a opção do Menu Lateral
        self.SetLateralMenu("Ambiente > Cadastros > Parâmetros")

        # Clica no botão/icone pesquisar
        self.SetButton("Pesquisar")

        backup_idwizard = self.idwizard[:]

        for line in self.camposCache:
            # Preenche o campo de Pesquisa
            self.SetValue("aCab", "Procurar por:", line['Procurar por:'])

            # Confirma a busca
            self.SetButton("Buscar")

            # Clica no botão/icone Editar
            self.SetButton("Editar")

            #self.idwizard = backup_idwizard[:]

            self.SetValue("aCab", 'Cont. Por', line['Cont. Por'])
            self.SetValue("aCab", 'Cont. Ing', line['Cont. Ing'])
            self.SetValue("aCab", 'Cont. Esp', line['Cont. Esp'])

            # Confirma a gravação de Edição
            self.SetButton("Salvar")
            self.idwizard = backup_idwizard[:]


    def close_modal(self):
        '''
        This method closes the last open modal in the screen.
        '''
        soup = self.get_current_DOM()
        modals = self.zindex_sort(soup.select(".tmodaldialog"), True)
        if modals and self.element_exists(By.CSS_SELECTOR, ".tmodaldialog .tbrowsebutton"):
            buttons = modals[0].select(".tbrowsebutton")
            if buttons:
                close_button = next(iter(list(filter(lambda x: x.text == self.language.close, buttons))))
                time.sleep(0.5)
                selenium_close_button = lambda: self.driver.find_element_by_xpath(xpath_soup(close_button))
                if close_button:
                    self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(close_button))))
                    self.Click(selenium_close_button())

    def check_mask(self, element):
        """
        Checks wether the element has a numeric mask.
        """
        reg = (r"^[1-9.\/-:]+|(@. )[1-9.\/-:]+")
        mask = element.get_attribute("picture")
        if mask is None:
            child = element.find_elements(By.CSS_SELECTOR, "input")
            if child:
                mask = child[0].get_attribute("picture")

        return (mask != "" and mask is not None and (re.search(reg, mask)))

    def apply_mask(self, string):
        """
        Removes special characters from received string.
        """
        caracter = (r'[.\/-]')
        if string[0:4] != 'http':
            match = re.search(caracter, string)
            if match:
                string = re.sub(caracter, '', string)

        return string

    def log_error(self, message, new_log_line=True):
        """
        Finishes execution of test case with an error and creates the log information for that test.
        """
        stack = list(map(lambda x: x.function, filter(lambda x: re.search('test_', x.function),inspect.stack())))[0]
        stack = stack.split("_")[-1]
        log_message = ""
        log_message += stack + " - " + message

        if new_log_line:
            self.log.new_line(False, log_message)
        self.log.save_file()
        self.Restart()
        self.assertTrue(False, log_message)

    def SetKey(self, key, grid=False, grid_number=None):
        """
        Press the desired key on the keyboard on the focused element.
        Supported keys: F1 to F12, Up, Down, Left, Right, Enter and Delete
        """
        supported_keys = {
            "F1" : Keys.F1,
            "F2" : Keys.F2,
            "F3" : Keys.F3,
            "F4" : Keys.F4,
            "F5" : Keys.F5,
            "F6" : Keys.F6,
            "F7" : Keys.F7,
            "F8" : Keys.F8,
            "F9" : Keys.F9,
            "F10" : Keys.F10,
            "F11" : Keys.F11,
            "F12" : Keys.F12,
            "UP" : Keys.UP,
            "DOWN" : Keys.DOWN,
            "LEFT": Keys.LEFT,
            "RIGHT": Keys.RIGHT,
            "DELETE" : Keys.DELETE,
            "ENTER": Keys.ENTER
        }

        #JavaScript function to return focused element if DIV or Input OR empty

        script = """
        var getActiveElement = () => {
	        if(document.activeElement.tagName.toLowerCase() == "input" || document.activeElement.tagName.toLowerCase() == "div"){
		        if(document.activeElement.attributes["id"]){
			        return document.activeElement.attributes["id"].value
		        }else if(document.activeElement.parentElement.attributes["id"]){
			        return document.activeElement.parentElement.attributes["id"].value
		        }
            }
	        return ""
        }

        return getActiveElement()
        """

        try:
            Id = self.driver.execute_script(script)
            if Id:
                element = self.driver.find_element_by_id(Id)
            else:
                element = self.driver.find_element(By.TAG_NAME, "html")

            if key.upper() in supported_keys:
                if key.upper() == "DOWN" and grid:
                    #self.UTSetValue('aItens','newline','0')
                    if grid_number is None:
                        grid_number = 0
                    self.grid_input.append(["", "", grid_number, True])
                else:
                    self.set_selenium_focus(element)
                    self.SendKeys(element, supported_keys[key.upper()])
            else:
                self.log_error("Key is not supported")

        except Exception as error:
            self.log_error(str(error))

    def SetFocus(self, field):
        """
        Set the current focus on the desired field.
        """
        Id = self.SetScrap(field, 'div', 'tget', 'Enchoice')
        element = self.driver.find_element_by_id(Id)
        self.set_selenium_focus(element)

    def down_grid(self):
        ActionChains(self.driver).key_down(Keys.DOWN).perform()

    def enter_grid(self):
        ActionChains(self.driver).key_down(Keys.ENTER).perform()

    def check_checkbox(self,campo,valor):
        print('time.sleep(1) - 2415')
        time.sleep(1)
        element = ''
        lista = self.driver.find_elements(By.CSS_SELECTOR, ".tcheckbox.twidget")
        for line in lista:
            if line.is_displayed() and line.get_attribute('name').split('->')[1] == campo:
                checked = "CHECKED" in line.get_attribute('class').upper()
                if valor != checked:
                    element = line
                    self.Click(line)
                    print('time.sleep(1) - 2425')
                    time.sleep(1)
                    break
        return element

    def check_radio(self,campo,valor):
        print('time.sleep(1) - 2431')
        time.sleep(1)
        element = ''
        lista = self.driver.find_elements(By.CSS_SELECTOR, ".tradiobutton.twidget")
        for line in lista:
            if line.is_displayed():
                lista2 = line.find_elements(By.CSS_SELECTOR, ".tradiobuttonitem")
                for line2 in lista2:
                    if line2.text.upper() == campo.upper():
                        element = line2
                        self.Click(line2)
                        print('time.sleep(1) - 2442')
                        time.sleep(1)
                        return element

    def result_checkbox(self,campo,valor):
        result = False
        print('time.sleep(1) - 2448')
        time.sleep(1)
        lista = self.driver.find_elements(By.CSS_SELECTOR, ".tcheckbox.twidget")
        for line in lista:
            if line.is_displayed() and line.get_attribute('name').split('->')[1] == campo:
                if "CHECKED" in line.get_attribute('class').upper():
                    result = True
        return result

    def get_closing_button(self, is_advpl):
        if is_advpl:
            Id = self.SetScrap(self.language.cancel, "div", "tbrowsebutton")
        else:
            Id = self.SetScrap(self.language.close, "div", "tbrowsebutton")
        return self.driver.find_element_by_id(Id)

    def is_advpl(self):
        return self.element_exists(By.CSS_SELECTOR, "div.tbrowsebutton", text=self.language.cancel)

    def clear_grid(self):
        self.btnenchoice = True
        self.grid_input = []
        self.grid_check = []

    def InputGrid(self, column, value, grid_number=0, new=False):
        self.grid_input.append([column, value, grid_number, new])

    def CheckGrid(self, line, column, value, grid_number=0):
        self.grid_check.append([line, column, value, grid_number])

    def LoadGrid(self):
        self.wait_enchoice()
        x3_dictionaries = ()
        inputs = list(map(lambda x: x[0], self.grid_input))
        checks = list(map(lambda x: x[1], self.grid_check))
        fields = list(filter(lambda x: "_" in x, inputs + checks))
        if fields:
            x3_dictionaries = self.get_x3_dictionaries(fields)

        initial_layer = 0
        if self.grid_input:
            soup = self.get_current_DOM()
            initial_layer = len(soup.select(".tmodaldialog"))

        for field in self.grid_input:
            print(field)
            if field[3] and field[0] == "":
                self.new_grid_line(field)
            else:
                self.fill_grid(field, x3_dictionaries, initial_layer)

        for field in self.grid_check:
            print(field)
            self.check_grid(field, x3_dictionaries)

        self.clear_grid()

    def fill_grid(self, field, x3_dictionaries, initial_layer):
        field_to_label = {}
        field_to_valtype = {}
        field_to_len = {}

        if x3_dictionaries:
            field_to_label = x3_dictionaries[2]
            field_to_valtype = x3_dictionaries[0]
            field_to_len = x3_dictionaries[1]

        while(self.element_exists(by=By.CSS_SELECTOR, selector=".tmodaldialog.twidget", position=initial_layer+1)):
            print("Waiting for container to be active")
            time.sleep(1)

        soup = self.get_current_DOM()

        containers = soup.select(".tmodaldialog.twidget")
        if containers:
            containers = self.zindex_sort(containers, True)

            grids = containers[0].select(".tgetdados")
            if not grids:
                grids = containers[0].select(".tgrid")

            grids = self.filter_displayed_elements(grids)
            if grids:
                headers = self.get_headers_from_grids(grids)

                column_name = ""
                if field[2] > len(grids):
                    self.log_error(self.language.messages.grid_number_error)

                row = self.get_selected_row(grids[field[2]].select("tbody tr"))
                if row:
                    columns = row.select("td")
                    if columns:
                        if "_" in field[0]:
                            column_name = field_to_label[field[0]]
                        else:
                            column_name = field[0]

                        if column_name not in headers[field[2]]:
                            self.log_error(self.language.messages.grid_column_error)

                        column_number = headers[field[2]][column_name]

                        current_value = columns[column_number].text.strip()

                        while(current_value.strip() != field[1].strip()):
                            selenium_column = lambda: self.driver.find_element_by_xpath(xpath_soup(columns[column_number]))
                            self.set_selenium_focus(selenium_column())

                            count = 0
                            while(not self.element_exists(by=By.CSS_SELECTOR, selector=".tmodaldialog.twidget", position=initial_layer+1)):
                                time.sleep(1)
                                self.set_selenium_focus(selenium_column())
                                if count % 2 != 0:
                                    self.SendKeys(selenium_column(), Keys.ENTER)
                                else:
                                    self.Click(selenium_column())
                                count+=1
                                time.sleep(1)

                            self.wait_element(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1)
                            soup = self.get_current_DOM()
                            new_container = self.zindex_sort(soup.select(".tmodaldialog.twidget"), True)[0]
                            child = new_container.select("input")
                            child_type = "input"
                            option_text = ""
                            if not child:
                                child = new_container.select("select")
                                child_type = "select"

                            if child_type == "input":

                                time.sleep(2)
                                selenium_input = lambda: self.driver.find_element_by_xpath(xpath_soup(child[0]))
                                self.wait_element(term=xpath_soup(child[0]), scrap_type=enum.ScrapType.XPATH)
                                valtype = selenium_input().get_attribute("valuetype")
                                lenfield = len(self.get_element_value(selenium_input()))
                                user_value = field[1]
                                if self.check_mask(selenium_input()):
                                    user_value = self.apply_mask(user_value)

                                self.wait.until(EC.visibility_of(selenium_input()))
                                self.set_selenium_focus(selenium_input())
                                time.sleep(1)
                                ActionChains(self.driver).send_keys_to_element(selenium_input(), user_value).perform()

                                if (("_" in field[0] and field_to_len != {} and int(field_to_len[field[0]]) > len(field[1])) or lenfield > len(field[1])):
                                    if (("_" in field[0] and field_to_valtype != {} and field_to_valtype[field[0]] != "N") or valtype != "N"):
                                        self.SendKeys(selenium_input(), Keys.ENTER)
                                    else:
                                        if not (re.match(r"[0-9]+,[0-9]+", user_value)):
                                            self.SendKeys(selenium_input(), Keys.ENTER)
                                        else:
                                            self.wait_element_timeout(term= ".tmodaldialog.twidget", scrap_type= enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, presence=False)
                                            if self.element_exists(by=By.CSS_SELECTOR, selector=".tmodaldialog.twidget", position=initial_layer+1):
                                                self.SendKeys(selenium_input(), Keys.ENTER)

                                self.wait_element(term=xpath_soup(child[0]), scrap_type=enum.ScrapType.XPATH, presence=False)
                                time.sleep(1)
                                current_value = self.get_selenium_text(selenium_column())

                            else:
                                option_text_list = list(filter(lambda x: field[1] == x[0:len(field[1])], map(lambda x: x.text ,child[0].select('option'))))
                                option_value_dict = dict(map(lambda x: (x.attrs["value"], x.text), child[0].select('option')))
                                option_value = self.get_element_value(self.driver.find_element_by_xpath(xpath_soup(child[0])))
                                option_text = next(iter(option_text_list), None)
                                if not option_text:
                                    self.log_error("Couldn't find option")
                                if (option_text != option_value_dict[option_value]):
                                    self.select_combo(child[0].find_parent().attrs['id'], field[1])
                                    if field[1] in option_text[0:len(field[1])]:
                                        current_value = field[1]
                                else:
                                    self.SendKeys(self.driver.find_element_by_xpath(xpath_soup(child[0])), Keys.ENTER)
                                    current_value = field[1]

                    else:
                        self.log_error("Couldn't find columns.")
                else:
                    self.log_error("Couldn't find rows.")
            else:
                self.log_error("Couldn't find grids.")

    def check_grid(self, field, x3_dictionaries):
        field_to_label = {}
        if x3_dictionaries:
            field_to_label = x3_dictionaries[2]

        while(self.element_exists(by=By.CSS_SELECTOR, selector=".tmodaldialog.twidget", position=3)):
            print("Waiting for container to be active")
            time.sleep(1)

        soup = self.get_current_DOM()

        containers = soup.select(".tmodaldialog.twidget")
        if containers:
            is_advpl = self.is_advpl()
            grid_selector = ""
            if is_advpl:
                grid_selector = ".tgetdados"
            else:
                grid_selector = ".tgrid"

            containers = self.zindex_sort(containers, True)
            grids = self.filter_displayed_elements(containers[0].select(grid_selector))
            if grids:

                headers = self.get_headers_from_grids(grids)
                column_name = ""
                if field[3] > len(grids):
                    self.log_error(self.language.messages.grid_number_error)

                rows = grids[field[3]].select("tbody tr")
                if rows:
                    if field[0] > len(rows):
                        self.log_error(self.language.messages.grid_line_error)

                    columns = rows[field[0]].select("td")
                    if columns:
                        if "_" in field[1]:
                            column_name = field_to_label[field[1]]
                        else:
                            column_name = field[1]

                        if column_name not in headers[field[3]]:
                            self.log_error(self.language.messages.grid_column_error)

                        column_number = headers[field[3]][column_name]
                        text = columns[column_number].text.strip()

                        field_name = f"({field[0]}, {column_name})"
                        self.LogResult(field_name, field[2], text)
                    else:
                        self.log_error("Couldn't find columns.")
                else:
                    self.log_error("Couldn't find rows.")
            else:
                self.log_error("Couldn't find grids.")

    def new_grid_line(self, field):
        soup = self.get_current_DOM()

        containers = soup.select(".tmodaldialog.twidget")
        if containers:
            is_advpl = self.is_advpl()
            grid_selector = ""
            if is_advpl:
                grid_selector = ".tgetdados"
            else:
                grid_selector = ".tgrid"

            containers = self.zindex_sort(containers, True)
            grids = self.filter_displayed_elements(containers[0].select(grid_selector))
            if grids:
                if field[2] > len(grids):
                    self.log_error(self.language.messages.grid_number_error)
                rows = grids[field[2]].select("tbody tr")
                row = self.get_selected_row(rows)
                if row:
                    columns = row.select("td")
                    if columns:
                        second_column = lambda: self.driver.find_element_by_xpath(xpath_soup(columns[1]))
                        # self.scroll_to_element(second_column())
                        self.driver.execute_script("$('.horizontal-scroll').scrollLeft(-400000);")
                        self.set_selenium_focus(second_column())
                        self.wait.until(EC.visibility_of_element_located((By.XPATH, xpath_soup(columns[0]))))
                        self.SendKeys(second_column(), Keys.DOWN)

                        while not(self.element_exists(by=By.CSS_SELECTOR, selector=f"{grid_selector} tbody tr", position=len(rows)+1)):
                            print("Waiting for the new line to show")
                            time.sleep(1)

                    else:
                        self.log_error("Couldn't find columns.")
                else:
                    self.log_error("Couldn't find rows.")
            else:
                self.log_error("Couldn't find grids.")

    def filter_displayed_elements(self, elements, reverse=False):
        #1 - Create an enumerated list from the original elements
        indexed_elements = list(enumerate(elements))
        #2 - Convert every element from the original list to selenium objects
        selenium_elements = list(map(lambda x : self.driver.find_element_by_xpath(xpath_soup(x)), elements))
        #3 - Create an enumerated list from the selenium objects
        indexed_selenium_elements = list(enumerate(selenium_elements))
        #4 - Filter elements based on "is_displayed()" and gets the filtered elements' enumeration
        filtered_selenium_indexes = list(map(lambda x: x[0], filter(lambda x: x[1].is_displayed(), indexed_selenium_elements)))
        #5 - Use List Comprehension to build a filtered list from the elements based on enumeration
        filtered_elements = [x[1] for x in indexed_elements if x[0] in filtered_selenium_indexes]
        #6 - Sort the result and return it
        return self.zindex_sort(filtered_elements, reverse)

    def get_x3_dictionaries(self, fields):

        prefixes = list(set(map(lambda x:x.split("_")[0] + "_" if "_" in x else "", fields)))
        regex = self.generate_regex_by_prefixes(prefixes)

        #caminho do arquivo csv(SX3)
        path = os.path.join(os.path.dirname(__file__), r'data\\sx3.csv')
        #DataFrame para filtrar somente os dados da tabela informada pelo usuário oriundo do csv.
        data = pd.read_csv(path, sep=';', encoding='latin-1', header=None, error_bad_lines=False,
                        index_col='Campo', names=['Campo', 'Tipo', 'Tamanho', 'Título', None], low_memory=False)
        df = pd.DataFrame(data, columns=['Campo', 'Tipo', 'Tamanho', 'Título', None])
        if not regex:
            df_filtered = df.query("Tipo=='C' or Tipo=='N' or Tipo=='D' ")
        else:
            df_filtered = df.filter(regex=regex, axis=0)

        #Retiro os espaços em branco da coluna Campo e Titulo.
        df_filtered['Título'] = df_filtered['Título'].map(lambda x: x.strip())
        df_filtered.index = df_filtered.index.map(lambda x: x.strip())

        dict_ = df_filtered.to_dict()

        return (dict_['Tipo'], dict_['Tamanho'], dict_['Título'])

    def generate_regex_by_prefixes(self, prefixes):
        filtered_prefixes = list(filter(lambda x: x != "", prefixes))
        regex = ""
        for prefix in filtered_prefixes:
            regex += "^" + prefix + "|"

        return regex[:-1]

    def get_current_DOM(self):
        return BeautifulSoup(self.driver.page_source,"html.parser")

    def get_headers_from_grids(self, grids):
        headers = []
        for item in grids:
            labels = item.select("thead tr label")
            keys = list(map(lambda x: x.text.strip(), labels))
            values = list(map(lambda x: x[0], enumerate(labels)))
            headers.append(dict(zip(keys, values)))
        return headers

    def get_selenium_text(self, element):
        return self.driver.execute_script("return arguments[0].innerText", element)

    def set_selenium_focus(self, element):
        self.driver.execute_script("window.focus; arguments[0].focus(); arguments[0].click()", element)

    def get_element_value(self, element):
        return self.driver.execute_script("return arguments[0].value", element)

    def field_exists(self, term, scrap_type, position=None, optional_term=None):
        if scrap_type == enum.ScrapType.TEXT:
            underline = (r'\w+(_)')
            match = re.search(underline, term)

            if match:
                Ret = self.element_exists(By.CSS_SELECTOR, "[name*='{}']".format(term) )
            else:
                Ret = self.element_exists(By.CSS_SELECTOR, "div",text = term )

            return Ret
        elif scrap_type == enum.ScrapType.CSS_SELECTOR:
            return self.element_exists(By.CSS_SELECTOR, term, position=position)
        elif scrap_type == enum.ScrapType.XPATH:
            return self.element_exists(By.XPATH, term)
        elif scrap_type == enum.ScrapType.MIXED:
            if optional_term:
                return self.element_exists(by=By.CSS_SELECTOR, text=term , selector=optional_term)
            else:
                return False
        else:
            return False

    def wait_element(self, term, scrap_type=enum.ScrapType.TEXT, presence=True, position=None, optional_term=None):
        if self.consolelog:
            print("Waiting...")
        if presence:
            while not self.field_exists(term, scrap_type, position, optional_term):
                print('time.sleep(3) 1338')
                time.sleep(0.1)
        else:
            while self.field_exists(term, scrap_type, position, optional_term):
                print('time.sleep(3) 1338')
                time.sleep(0.1)

    def wait_element_timeout(self, term, scrap_type=enum.ScrapType.TEXT, timeout=5.0, step=0.1, presence=True, position=None, optional_term=None):
        if presence:
            count = step
            while count < timeout:
                time.sleep(step)
                count+=step
                if self.field_exists(term, scrap_type, position, optional_term):
                    break
        else:
            count = step
            while count < timeout:
                time.sleep(step)
                count+=step
                if not self.field_exists(term, scrap_type, position, optional_term):
                    break

    def get_selected_row(self, rows):
        filtered_rows = list(filter(lambda x: len(x.select("td.selected-cell")), rows))
        if filtered_rows:
            return next(iter(filtered_rows))

    def SetFilePath(self,value):
        self.wait_element("Nome do Arquivo:")
        element = self.driver.find_element(By.CSS_SELECTOR, ".filepath input")
        if element:
            self.driver.execute_script("document.querySelector('#{}').value='';".format(element.get_attribute("id")))
            self.SendKeys(element, value)
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".tremoteopensave button")
        if elements:
            for line in elements:
                if line.text.strip().upper() == "ABRIR":
                    self.Click(line)
                    break

    def MessageBoxClick(self, button_text):
        self.wait_element(".messagebox-container", enum.ScrapType.CSS_SELECTOR)

        content = self.driver.page_source
        soup = BeautifulSoup(content,"html.parser")
        container = soup.select(".messagebox-container")
        if container:
            buttons = container[0].select(".ui-button")
            button = list(filter(lambda x: x.text.lower() == button_text.lower(), buttons))
            if button:
                selenium_button = self.driver.find_element_by_xpath(xpath_soup(button[0]))
                self.Click(selenium_button)

    def get_enchoice_button_ids(self, layer):
        soup = self.get_current_DOM()
        current_layer = self.zindex_sort(soup.select(".tmodaldialog"), False)[layer - 1]
        buttons = list(filter(lambda x: x.text.strip() != "", current_layer.select(".tpanel button")))
        return list(map(lambda x: x.parent.attrs["id"], buttons))

    def CheckView(self, text, element_type="help"):
        '''
        Checks if a certain text is present in the screen at the time.
        '''
        if element_type == "help":
            self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.MIXED, timeout=2.5, step=0.5, optional_term=".tsay")
            if not self.element_exists(By.CSS_SELECTOR, ".tsay",text = text):
                self.invalid_fields.append(self.language.messages.text_not_found)
            else:
                self.SetButton(self.language.close)



# -*- coding: utf-8 -*-
"""
Created on Tue May 30 09:21:13 2017

@author: renan.lisboa
"""
import re
import csv
import time
import numpy as np
import pandas as pd
import unittest
import inspect
import socket
import sys
import os
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
        
        self.close_element = ''
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

        self.browse = True
        self.advpl = True
        self.proximo = True
        self.Ret = False
        self.refreshed = False
        self.consolelog = True
        self.passfield = False
        self.btnenchoice = True
        self.elementDisabled = False
        self.numberOfTries = 0

        self.invalid_fields = []
        self.log = Log(console = self.consolelog)
        self.log.station = socket.gethostname()

    def set_prog_inic(self, initial_program='SIGAADV'):
        '''
        Method that defines the program to be started
        '''
        if initial_program:
            self.initial_program = initial_program
        try:
            Id = self.SetScrap('inputStartProg', 'div', '')
            element = self.driver.find_element_by_id(Id)
            element.clear()
            self.SendKeys(element, self.initial_program)
        except:
            self.proximo = False

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
            time.sleep(2) 
            Id = self.SetScrap(self.language.user, 'div', 'tget')
            if self.consolelog:
                print('SetUsr ID: %s' %Id)
            element = self.driver.find_element_by_id(Id)              
            self.DoubleClick(element)
            self.SendKeys(element, Keys.HOME)
            self.SendKeys(element, self.config.user)

            resultado = self.UTCheckResult('', '', self.config.user, 0, Id, 'input')
            if resultado != self.config.user:
                print('Conteúdo do campo usuário não preenchido. Buscando...')
                self.set_user()
            self.log.user = self.config.user
        except Exception as error:
            print(error)
            self.proximo = False
            if self.consolelog:
                print("Não encontrou o campo Usuário")

    def set_password(self):
        """
        Complete the system password.
        """
        try:
            Id = self.SetScrap(self.language.password, 'div', 'tget')
            if self.consolelog:
                print('SetUsr ID: %s' %Id)
            element = self.driver.find_element_by_id(Id)
            time.sleep(2)
            self.DoubleClick(element)
            self.SendKeys(element, Keys.HOME)
            self.SendKeys(element, self.config.password)
        except:
            self.proximo = False
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
            self.proximo = False
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
            self.proximo = False
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
            self.proximo = False
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
            self.proximo = False
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
        else:
            self.proximo = False

    def wait_enchoice(self):
        Ret = ""
        if self.btnenchoice:
            self.btnenchoice = False
            while not Ret:
                Ret = self.SetScrap(self.language.cancel,"div","tbrowsebutton",'wait','',0,'',3)#Procuro botão de cancelar advpl antigo
                if Ret:
                    self.advpl = True
                    self.cClass = 'tgetdados'
                    self.close_element = self.driver.find_element_by_id(Ret)
                if not Ret:
                    Ret = self.SetScrap(self.language.close,"div","tbrowsebutton",'wait','',0,'',3)#Procuro botão de fechar advpl mvc
                    if Ret:
                        self.advpl = False
                        self.cClass = 'tgrid'
                        self.IdClose = Ret
                        self.close_element = self.driver.find_element_by_id(Ret)
            return Ret

   
    def wait_browse(self,searchMsg=True):
        Ret = ''
        endTime =   time.time() + 60
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
            if "CFG" in self.log.program:#TODO VERIFICAR ESTE TRECHO
                self.advpl = False
                self.passfield = True 
            element = self.driver.find_element_by_id(Id)
            self.DoubleClick(element)
            self.SendKeys(element, Keys.BACK_SPACE)
            self.SendKeys(element, self.rotina)
            element2 = self.driver.find_element_by_xpath("//div[@id='%s']/img" %Id)
            self.Click(element2)
        else:
            self.proximo = False
        self.rota = 'SetRotina'

    def set_enchoice(self, campo='', valor='', cClass='', args='', visibility='', Id='', disabled=False, tries=100):
        '''
         Method that fills the enchoice.
        '''
        if tries == 10:
            self.numberOfTries = 0
            if self.elementDisabled and self.consolelog:
            	print("Element is Disabled")
            self.LogResult(field=campo, user_value=disabled, captured_value=True, disabled_field=True)
            self.log.save_file()
            self.Restart()
            self.assertTrue(False, self.create_message(['', campo],enum.MessageType.DISABLED))
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

                resultado = self.UTCheckResult('', campo, valor, 0, Id, 'input')
                tam_interface = self.lenvalorweb
                if valsub != valor:
                    tam_valorusr = len(valsub)
                else:
                    tam_valorusr = len(valor)
                element = self.driver.find_element_by_id(Id)
                self.scroll_to_element(element)#posiciona o scroll baseado na height do elemento a ser clicado.
                try:
                    if self.classe == 'tcombobox':
                        self.select_combo(Id, valor)
                    else:
                        time.sleep(1)
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
                            selector = "#{} input".format(Id) 
                            while(tries < 3):
                                self.focus(element)
                                self.Click(element)
                                self.SendKeys(element, valor)
                                current_value = self.driver.execute_script("return document.querySelector('#{} input').value".format(Id))
                                if self.apply_mask(current_value).strip() == valor:
                                    break
                                tries+=1
                        else:
                            self.SendKeys(element, valor)

						# """childPresence = self.children_exists(element, By.CSS_SELECTOR, "img[src*=fwskin_icon_lookup]") TODO verificar tratamento do campo com consulta padrão.
                        # if self.classe == "tget" and childPresence:
                        #     for x in range(0, 3):i
                        #         self.Click(element)
                        #         self.SendKeys(element, Keys.ENTER)
                        # """
                        if tam_valorusr < tam_interface:
                            if self.valtype == 'N':
                                self.SendKeys(element, Keys.ENTER)
                            else:
                           		self.SendKeys(element, Keys.TAB)
                except Exception as error:
                    if self.consolelog:
                        print(error)
                    self.SetButton(self.language.cancel)
                    self.assertTrue(False, error)
                time.sleep(1)
                resultado = self.UTCheckResult('', campo, valor, 0, Id, 'input')

                if self.consolelog and resultado != "":
                    print(resultado)

                if resultado.lower() != str(valor).strip().lower() and not self.passfield and not self.valtype == 'N': #TODO AJUSTAR ESTE PONTO.
                    if self.elementDisabled:
                        self.numberOfTries += 1
                        self.set_enchoice(campo=campo, valor=valor, cClass='', args='', visibility='', Id=Id, disabled=disabled, tries=self.numberOfTries)
                    else:
                        if tries < 103:
                            self.set_enchoice(campo=campo, valor=valor, cClass='', args='', visibility='', Id=Id, disabled=disabled, tries=tries)
                        else:
                            self.log_error("Error trying to input value")
                elif self.passfield:
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
            combo.select_by_visible_text(valor)
        return valor

    def SetGrid(self, ChkResult=0):
        """
        Preenche a grid baseado nas listas self.gridcpousr e self.Table
        """
        Ret = ''
        self.btnenchoice = True
        Ret = self.wait_enchoice()#Aguardo o carregamento dos componentes da enchoice.
        self.rota = "SetGrid"
        if self.fillTable():    # Se self.Table estiver preenchido com campos da tabela que o usuario quer testar, não deve executar SearchField() novamente.
            self.SearchField()  # Obtem a caracteristica dos campos da grid, gerando a lista self.Table

        if Ret:
            element = self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'tmodaldialog.twidget'))) 
            # as duas linhas abaixo são somente documentação
            #element = self.driver.find_element_by_xpath("//div[@id='COMP7626']/div[1]/table/tbody/tr[@id='0']/td[@id='1']") # para clicar no segundo campo da 1a linha do grid
            #element = self.driver.find_element_by_xpath("//div[@id='COMP7626']/div[1]/table/tbody/tr[@id='1']/td[@id='1']") # para clicar no segundo campo da 2a linha do grid
            self.lineGrid = 0

            for campo, valor, linha in self.gridcpousr:
                if campo == "newline" or (ChkResult and linha and ((linha - 1) != self.lineGrid)):
                    element = self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'tmodaldialog.twidget')))
                    self.SendKeys(element, Keys.DOWN)#element.send_keys(Keys.DOWN)
                    self.lineGrid += 1
                    time.sleep(3)
                else:
                    #coluna = self.Table[2].index("M->%s" %campo)
                    coluna = self.Table[1].index(campo)
                    if self.consolelog:
                        print('Posicionando no campo %s' %campo)
                    # controla se a celula esta posicionada onde a variavel 'coluna' esta indicando e se a celula foi preenchida com o conteúdo da variavel 'valor'.
                    while self.cawait(coluna, campo, valor, element, ChkResult):

                        Id = self.SetScrap('', 'div', self.cClass, 'setGrid')
                        if Id:
                            # nao estava posicionado na celula correta então tenta novamente e volta para a funcao cawait()
                            if self.advpl:
                                element = self.driver.find_element_by_xpath("//div[@id='%s']/div[1]/table/tbody/tr[@id=%s]/td[@id=%s]" % ( str(Id), str(self.lineGrid), str(coluna) ) )
                            else:
                                element = self.driver.find_element_by_xpath("//div[@id='%s']/div/table/tbody/tr[@id=%s]/td[@id=%s]/div" % ( str(Id), str(self.lineGrid), str(coluna) ) )
                                #//div[@id='COMP8015']/div/table/tbody/tr/td[3]/div
                            self.lastColweb = coluna
                            time.sleep(1)
                            self.wait.until(EC.element_to_be_clickable((By.ID, Id)))
                            self.Click(element)
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

        if self.advpl:
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
            
        if not self.advpl:
            for line in grid:
                if line.attrs['class'][5] == 'cell-mode':
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
                time.sleep(1)#tempo de espera para cada verificação.
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
        tooltipId = ''
        tooltipState = False
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
                menuItens = {self.language.copy: 's4wb005n.png',self.language.cut: 's4wb006n.png',self.language.paste: 's4wb007n.png',self.language.calculator: 's4wb008n.png',self.language.spool: 's4wb010n.png',self.language.ajuda: 's4wb016n.png',self.language.exit: 'final.png',self.language.search: 's4wb011n.png', self.language.folders: 'folder5.png', self.language.generate_differential_file: 'relatorio.png',self.language.add: 'bmpincluir.png', self.language.view: 'bmpvisual.png','Editar': 'editable.png',self.language.delete: 'excluir.png',self.language.filter: 'filtro.png'}
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
                                            if len(x.attrs['class']) > 3:
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
        if "style" in element.attrs and "z-index:" in element.attrs['style']:
            zindex = int(element.attrs['style'].split("z-index:")[1].split(";")[0].strip())
        
        return zindex

    def SearchBrowse(self, descricao='', chave='', indice=False, placeholder=''):
        '''
        Mètodo que pesquisa o registro no browse com base no indice informado.
        '''
        self.btnenchoice = True
        Ret = self.wait_browse() #Verifica se já efetuou o fechamento da tela

        if Ret:
            self.savebtn = ''
            #Caso solicite para alterar o indice
            #if indice:
            #Faz a busca do icone para clique e seleção do indice.
            Id = self.SetScrap('fwskin_seekbar_ico.png', '', 'tpanel', 'indice', placeholder)
            if Id:
                element = self.driver.find_element_by_xpath("//div[@id='%s']/button" %Id)
                if self.rota == 'SetRotina' or self.rota == 'EDAPP':
                    self.SetScrap(self.language.view, 'div', 'tbrowsebutton', 'wait', '', '', '', 10)
                    self.rota = ''
                self.Click(element)
                #seleciona a busca do indice baseado na descrição ex: Filial+numero
                if indice:
                    self.SetScrap(descricao, 'div', 'tradiobutton', 'indice', 'detail')
                else:
                    self.SetScrap(placeholder, 'div', 'tradiobutton', 'indicedefault', 'detail')
                self.placeHolder(placeholder, chave)
                # self.data_check(descricao,chave)
            else:
                self.proximo = False
            pass

    def placeHolder(self, placeholder='', chave=''):
        Id = self.SetScrap('placeHolder', 'div', 'tget', args2=placeholder)
        if Id:
            element = self.driver.find_element_by_id(Id)
            self.Click(element)
            self.SendKeys(element, chave)
            time.sleep(1)
            self.Click(element)
            time.sleep(1)
            element2 = self.driver.find_element_by_xpath("//div[@id='%s']/img" %Id)
            time.sleep(2)
            self.DoubleClick(element2)
            time.sleep(1)
            self.DoubleClick(element)
            self.SendKeys(element, Keys.BACK_SPACE)
            return True

    # VISAO 3 - Tela inicial
    def ProgramaInicial(self, initial_program="", environment=""):
        self.set_prog_inic(initial_program)
        self.set_enviroment()
        self.SetButton('Ok', 'startParameters', '', 60, 'button', 'tbutton')

    def Usuario(self):
        """
        Preenchimento da tela de usuario
        """
        self.set_user()
        self.set_password()
        if self.proximo:
            self.SetButton(self.language.enter, '', '', 60, 'button', 'tbutton')

    def Ambiente(self, trocaAmb=False):
        """
        Preenche a tela de data base do sistema
        """
        if self.proximo:
            self.set_based_date(trocaAmb)
        if self.proximo:
            self.set_group(trocaAmb)
        if self.proximo:    
            self.set_branch(trocaAmb)
        if self.proximo:
            self.set_module_of_system(trocaAmb)
        if self.proximo:
            if trocaAmb:
                label = self.language.confirm
            else:
                label = self.language.enter

            self.SetButton(label,'','',60,'button','tbutton')

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
        
        self.ProgramaInicial(initial_program)

        self.Usuario()
        self.Ambiente()

        while(not self.element_exists(By.CSS_SELECTOR, ".tmenu")):
            self.close_modal()

        self.set_log_info()

    def UTProgram(self, rotina):
        """
        Preenche a tela de rotina
        """
        self.rotina = rotina
        self.SetRotina()
        self.wait_browse() # Wait to load elements in browser
    
    def UTSetValue(self, cabitem, campo, valor, linha=0, chknewline=False, disabled=False):
        """
        Indica os campos e o conteudo do campo para preenchimento da tela.
        """
        #time.sleep(1)
        self.elementDisabled = False
        if cabitem == "aCab":
            self.set_enchoice(campo, valor, '', 'Enchoice', '', '', disabled)
        elif cabitem == "aItens":
            # identifica nova linha quando executado através do metodo UTCheckResult
            if chknewline and self.CpoNewLine == campo:
                self.UTAddLine()
            # quando for grid, guarda os campos e conteúdo na lista
            self.gridcpousr.append([campo, valor, linha])
            # guarda o campo de referencia para posteriormente adicionar nova linha
            if chknewline and len(self.gridcpousr) == 1:
                self.CpoNewLine = campo
            # indica para o metodo VldData a rota que deverá ser seguida    
            self.rota = 'SetValueItens'
            self.field = campo

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

    def UTAddLine(self):
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

            '''
            # Se a celula nao estiver posicionada onde a variavel 'coluna' esta indicando
            if self.lastColweb != str(coluna):
                print('Posicionando na coluna %s' %str(coluna))
                # return true fara com que entre novamente aqui( cawait ) e tente focar na celula que a variavel 'coluna' esta indicando
                return True
            # A celula esta posicionada conforme a variavel 'coluna' indicou !
            else:
            '''
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
                            self.SendKeys(element, Keys.ENTER)#element.send_keys(Keys.ENTER)
                            time.sleep(1)
                            self.SendKeys(element, valsub)#element.send_keys(valor)
                            self.SendKeys(element, Keys.ENTER)#element.send_keys(Keys.ENTER)

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
                        self.SendKeys(element, Keys.ENTER)#element.send_keys(Keys.ENTER)
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
                       
                            time.sleep(1)
                            if valsub != valor and self.check_mask(element):
                                self.SendKeys(element, valsub)#element.send_keys(valsub)
                            else:
                                self.SendKeys(element, valor)#element.send_keys(valor)
                            if len(valor) < self.lenvalorweb:
                                self.SendKeys(element, Keys.ENTER)#element.send_keys(Keys.ENTER)
                        #time.sleep(3)
                        # return true fara com que entre novamente aqui( cawait ) para garantir que os dados foram preenchidos corretamente.
                        return True
                    else:
                        # o campo foi preenchido corretamente, então o processo analisará o próximo campo contido em gridcpousr.
                        return False
        except Exception as error:
            if self.consolelog:
                print(error)
            return True

    def UTCheckResult(self, cabitem, campo, valorusr, linha=0, Id='', args1=''):
        """
        Validação de interface
        """
        if args1 != 'input' and cabitem != 'help':
            self.wait_enchoice()
            self.rota = "UTCheckResult"
        valorweb = ''
        if not Id:
            if cabitem == 'aCab':
                Id = self.SetScrap(campo, 'div', 'tget', 'Enchoice')
            elif cabitem == 'Virtual':
                Id = self.SetScrap(campo, 'div', 'tsay', 'Virtual')
            elif cabitem == 'help':
                Id = self.SetScrap(valorusr, '','tsay twidget dict-tsay align-left transparent','caHelp')
        if cabitem != 'aItens':
            if Id:
                element = self.driver.find_element_by_id(Id)
                if args1 != 'input':
                    self.Click(element)
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
            if args1 != 'input':
                self.LogResult(campo, valorusr, valorweb)
        else:
            self.UTSetValue(cabitem, campo, valorusr, linha, True)
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

    def LogResult(self, field, user_value, captured_value, call_grid=False, disabled_field=False):
        '''
        Log the result of comparison between user value and captured value
        '''
        txtaux = ""
        message = ""
        if call_grid:
            txtaux = 'Item: %s - ' %str(self.lineGrid + 1)

        if disabled_field and not user_value:
            message = self.create_message([txtaux, field], enum.MessageType.DISABLED)
        elif disabled_field and user_value:
            message = self.create_message([txtaux, field], enum.MessageType.DISABLED)
        elif user_value != captured_value and not disabled_field:
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
        self.LogOff()
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
                if (line.string == self.language.error_log):
                    self.SetButton(self.language.details,cClass='tbutton',searchMsg=False)
                    self.driver.save_screenshot( self.GetFunction() +".png")
                    self.log.new_line(False, self.language.error_log_print)
                    self.log.save_file()
                    self.assertTrue(False, self.language.error_log_print)

    def SearchHelp(self,soup):
        '''
        This method is called to treat Help messages
        '''
        lista = soup.find_all('div', class_=('workspace-container')) # Leva como base div inicial
        if lista:
            lista = lista[0].contents # Pega filhos da tela principal
            for line in lista:
                message = ""
                if line.text == self.language.error_msg_required:
                    message = self.language.error_msg_required
                    self.search_help_error(message)
                elif self.language.help in line.text and self.language.problem in line.text:     
                    message = line.text
                    self.search_help_error(message)
                
    def search_help_error(self, message):
        '''
        This method is part of SearchHelp internal functionality
        '''
        self.driver.save_screenshot( self.GetFunction() +".png")
        self.SetButton(self.language.close,cClass='tbutton',searchMsg=False)
        self.savebtn = ''
        self.Click(self.close_element)
        if not self.advpl:
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

    def children_exists(self, element, by, childSelector):
        '''
        Returns a boolean if children element exists inside parent.
        '''
        children = element.find_elements(by, childSelector)
        return len(children) > 0
    
    
    def element_exists(self, by, selector, position='',text=''):
        '''
        Returns a boolean if element exists on the screen
        '''
        if not position and not text:
            element_list = self.driver.find_elements(by, selector)
            return len(element_list) > 0
        elif position and not text:
            element_list = self.driver.find_elements(by, selector)
            return len(element_list) >= position
        else:
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

        menuitens = list(map(str.strip, menuitens.split(">")))

        menuId = self.SetScrap(cClass="tmenu")
        menu = self.driver.find_element_by_id(menuId)

        for menuitem in menuitens:
            menu = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#{}".format(menu.get_attribute("id")))))
            self.wait_elements_load("#{} .tmenuitem".format(menu.get_attribute("id")))
            subMenuElements = menu.find_elements(By.CSS_SELECTOR, ".tmenuitem")
            submenu = ""   
            for child in subMenuElements:
                if child.text.startswith(menuitem):
                    submenu = child
                    break
            if subMenuElements and submenu:
                self.scroll_to_element(submenu)
                self.Click(submenu)
                menu = submenu
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

    def wait_elements_load(self, selector):
        '''
        Wait for elements defined by the CSS Selector to be present on the screen
        '''
        self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))

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
        stack = list(map(lambda x: x.function, filter(lambda x: re.search('test_', x.function),inspect.stack())))[0].split("CT")[1]
        log_message = ""
        log_message += stack + " -"

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
        self.wait_elements_load(".tmodaldialog")

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

    def SetButton(self, button, args1='wait', args2='', args3=10, tag='div', cClass='tbrowsebutton',searchMsg = True):
        '''
        Método que efetua o clique nos botão da interface
        '''
        try:
            Id  = ''
            if self.VldData():
                if (button.lower() == self.language.Ok.lower()) and args1 != 'startParameters':
                    Id = self.SetScrap(button, tag, '', 'btnok') 
                    if Id:
                        element = self.driver.find_element_by_id(Id)
                        self.Click(element)
                else:
                    if button in self.language.no_actions:
                        Id = self.SetScrap(button, tag, cClass, '', '', '', '', 60, searchMsg)
                    else:
                        Id = self.SetScrap(button, tag, cClass, args1, '', '', '', args3, searchMsg)
                        if not Id:
                            Id = self.SetScrap(self.language.other_actions, tag, cClass, args1,'', '', '', args3,searchMsg)
                            element = self.driver.find_element_by_id(Id)
                            self.Click(element)
                            if Id:
                                self.SetItemMen(button, '', 'menuitem')
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
                            self.browse = False
                            if args1 != '' and args1 != 'wait':#se for botão incluir com subitens
                                self.advpl = False
                                Id = self.SetScrap(args1, 'li', 'tmenupopupitem')
                                if Id:
                                    element = self.driver.find_element_by_id(Id)
                                    self.Click(element)
                        elif button == self.language.edit or button == self.language.view: # caso não seja outras ações do Browse.
                            self.browse = False
                    else:
                        self.proximo = False
            if button == self.language.edit or button == self.language.view or button == self.language.delete or button == self.language.add:
                if not self.element_exists(By.CSS_SELECTOR, ".ui-dialog"):
                    self.wait_enchoice()
                    self.btnenchoice = True
        except ValueError as error:
            if self.consolelog:
                print(error)
            self.Restart()
            self.assertTrue(False, "Campo %s não encontrado" %error.args[0])
        except Exception as error:
            if self.consolelog:
                print(error)
            self.Restart()
            self.assertTrue(False) 


    def SetFilial(self, filial):
        """
        Método que seta a filial na inclusão
        """
        Ret = self.placeHolder('', filial)
        if Ret:
            self.SetButton('OK','','',60,'div','tbutton')
            self.wait_enchoice()
            
    def UTWaitWhile(self,itens):
        '''
        Search string that was sent and wait while condition is true
        e.g. "Item1,Item2,Item3"
        '''
        self.search_text(itens,True)

    def UTWaitUntil(self,itens):
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
            self.proximo = False
            if self.consolelog:
                print("Não encontrou o campo Pesquisar")
        self.rota = 'EDAPP'

    def ClickFolder(self, item):
        '''
        Método que efetua o clique na aba
        ''' 
        self.rota = "ClickFolder"
        if self.close_element:
            self.move_element(self.close_element) # Retira o ToolTip dos elementos focados.
        self.wait_enchoice()
        #self.advpl = False
        if self.VldData():
            try:#Tento pegar o elemento da aba de forma direta sem webscraping
                element = self.driver.find_element_by_link_text(item)
            except:#caso contrário efetuo o clique na aba com webscraping    
                Id = self.SetScrap(item, '', 'button-bar', 'abaenchoice')
                if Id:
                    element = self.driver.find_element_by_id(Id)
            
            self.scroll_to_element(element)#posiciona o scroll baseado na height do elemento a ser clicado.
            self.Click(element)
    
    def ClickBox(self, labels):
        '''
        Método que efetua o clique no checkbox
        '''
        listas = labels.split(",")
        self.wait_enchoice()#Aguardo o carregamento dos componentes da enchoice.
        if labels == 'Todos':
            Id = self.SetScrap('Inverte Selecao', 'label', 'tcheckbox')
            if Id:
                element = self.driver.find_element_by_id(Id)
                self.Click(element)
        else:
            table = self.SetTable()

            while not table:
                print("Esperando table")    
                table = self.SetTable()
            
            tables = self.driver.find_elements(By.CSS_SELECTOR, self.grid_class)
            zindex = 0
            grid_id = ""
            for tab in tables:
                zindex_atual = int(tab.get_attribute("style").split("z-index:")[1].split(";")[0].strip())
                if zindex < zindex_atual:
                    zindex = zindex_atual
                    grid_id = tab.get_attribute("Id")
            
            grid = self.driver.find_element(By.ID, grid_id)

            for lista in listas:
                for x in range(0, len(table)):
                    for index, y in enumerate(table[x][1]):
                        if lista.strip() == y[1]:
                            elements_list = grid.find_elements(By.CSS_SELECTOR, "td[id='1']")
                            self.scroll_to_element(elements_list[index])
                            self.Click(elements_list[index])
                            time.sleep(1)
                            self.SendKeys(elements_list[index], Keys.ENTER)

    def close_modal(self):
        '''
        This method closes the last open modal in the screen.
        '''
        modals = self.driver.find_elements(By.CSS_SELECTOR, ".tmodaldialog")
        if modals and self.element_exists(By.CSS_SELECTOR, ".tmodaldialog .tbrowsebutton"):
            modals.sort(key=lambda x: x.get_attribute("style").split("z-index:")[1].split(";")[0], reverse=True)
            close_button = list(filter(lambda x: x.text == self.language.close, modals[0].find_elements(By.CSS_SELECTOR, ".tbrowsebutton")))
            if close_button:
                self.Click(close_button[0])
                            
    def check_mask(self, element):
        """
        Checks wether the element has a numeric mask.
        """
        reg = (r"(@. )?[1-9.\/-]+")
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
        if new_log_line:
            self.log.new_line(False, message)
        self.log.save_file()
        self.assertTrue(False, message)

    def SetFocus(self, field):
        """
        Set the current focus on the desired field.
        """
        Id = self.SetScrap(field, 'div', 'tget', 'Enchoice')
        element = self.driver.find_element_by_id(Id)
        self.focus(element)

    def focus(self, element):
        """
        Set the focus on the element
        """
        Id = element.get_attribute("id")
        selector = "#{}".format(Id)
        if(self.children_exists(element, By.CSS_SELECTOR, "input")):
            selector = "#{} input".format(Id)
        script = "window.focus; elem = document.querySelector('"+ selector +"'); elem.focus(); elem.click()"
        self.driver.execute_script(script)
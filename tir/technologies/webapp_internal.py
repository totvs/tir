import re
import csv
import time
import pandas as pd
import unittest
import inspect
import socket
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
import tir.technologies.core.enumerations as enum
from tir.technologies.core.log import Log
from tir.technologies.core.config import ConfigLoader
from tir.technologies.core.language import LanguagePack
from tir.technologies.core.third_party.xpath_soup import xpath_soup
from tir.technologies.core.base import Base

class WebappInternal(Base):
    def __init__(self, config_path=""):
        super().__init__(config_path)
        self.base_container = ".tmodaldialog"

        self.LastId = []
        self.LastIdBtn = []
        self.gridcpousr = []
        self.Table = []
        self.lenbutton = []
        self.idwizard = []

        self.grid_counters = {}
        self.grid_input = []
        self.grid_check = []
        self.date = ''
        self.rota = ''
        self.CpoNewLine = ''
        self.classe = ''
        self.valtype = ''
        self.savebtn = ''
        self.idcomp = ''
        self.lenvalorweb = ''
        self.grid_value = ''
        self.grid_class = ''
        self.initial_program = 'SIGAADV'

        self.lineGrid = 0
        self.index = 0
        self.lastColweb = 0

        self.Ret = False
        self.refreshed = False
        self.consolelog = True
        self.btnenchoice = True
        self.elementDisabled = False
        self.numberOfTries = 0

        self.errors = []

        self.camposCache = []
        self.parametro = ''
        self.backupSetup = dict()

        self.used_ids = []

    def set_program(self, program):
        '''
        [Internal]
        Method that sets the program in the initial menu search field.
        '''

        self.wait_element(term="[name=cGet]", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        soup = self.get_current_DOM()
        tget = next(iter(soup.select("[name=cGet]")), None)
        if tget:
            tget_img = next(iter(tget.select("img")), None)

            if tget_img is None:
                self.log_error("Couldn't find Program field.")

            s_tget = lambda : self.driver.find_element_by_xpath(xpath_soup(tget))
            s_tget_img = lambda : self.driver.find_element_by_xpath(xpath_soup(tget_img))

            self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(tget))))
            self.double_click(s_tget())
            self.set_element_focus(s_tget())
            self.send_keys(s_tget(), Keys.BACK_SPACE)
            self.send_keys(s_tget(), program)
            self.click(s_tget_img())

            self.rota = 'SetRotina'

    def input_value(self, field, value, ignore_case=True):
        """
        [Internal]
        [returns Bool]
        Sets a value in an input element.
        Returns True if succeeded, False if it failed.
        """
        success = False
        endtime = time.time() + 60

        while(time.time() < endtime and not success):
            unmasked_value = self.remove_mask(value)

            print(f"Searching for: {field}")

            if re.match(r"\w+(_)", field):
                elements_list = self.web_scrap(f"[name*='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)
                element = next(iter(filter(lambda x: re.search(f"{field}$", x.attrs["name"]), elements_list)), None)
            else:
                element = next(iter(self.web_scrap(field, scrap_type=enum.ScrapType.TEXT, label=True)), None)

            if not element:
                continue

            #preparing variables that would be used
            main_element = element
            element_id = element.attrs["id"]

            element_first_children = next((x for x in element.contents if x.name in ["input", "select"]), None)
            if element_first_children is not None:
                main_element = element_first_children

            input_field = lambda: self.driver.find_element_by_xpath(xpath_soup(main_element))

            valtype = "C"
            main_value = unmasked_value if value != unmasked_value and self.check_mask(input_field()) else value

            interface_value = self.get_web_value(input_field())
            current_value = interface_value.strip()
            interface_value_size = len(interface_value)
            user_value_size = len(main_value)

            if not input_field().is_enabled() or "disabled" in main_element.attrs:
                self.log_error(self.create_message(['', field],enum.MessageType.DISABLED))

            if main_element.name == "input":
                valtype = main_element.attrs["valuetype"]

            self.scroll_to_element(input_field())

            try:
                #Action for Combobox elements
                if "tcombobox" in element.attrs["class"]:
                    self.wait.until(EC.visibility_of(input_field()))
                    self.set_element_focus(input_field())
                    self.select_combo(element_id, main_value)
                #Action for Input elements
                else:
                    self.wait.until(EC.visibility_of(input_field()))
                    self.wait.until(EC.element_to_be_clickable((By.ID, element_id)))
                    self.double_click(input_field())

                    #if Character input
                    if valtype != 'N':
                        self.send_keys(input_field(), Keys.DELETE)
                        self.send_keys(input_field(), Keys.HOME)
                        self.send_keys(input_field(), main_value)
                    #if Number input
                    else:
                        tries = 0
                        while(tries < 3):
                            self.set_element_focus(input_field())
                            self.send_keys(input_field(), Keys.DELETE)
                            self.send_keys(input_field(), Keys.BACK_SPACE)
                            self.click(input_field())
                            input_field().send_keys(main_value)
                            current_number_value = self.get_web_value(input_field())
                            if self.remove_mask(current_number_value).strip() == main_value:
                                break
                            tries+=1

                    if user_value_size < interface_value_size:
                        self.send_keys(input_field(), Keys.ENTER)

                    if self.check_mask(input_field()):
                        current_value = self.remove_mask(self.get_web_value(input_field()).strip())
                    else:
                        current_value = self.get_web_value(input_field()).strip()

                    if self.consolelog and current_value != "":
                        print(current_value)

                if "tcombobox" in element.attrs["class"]:
                        current_value = current_value[0:len(str(value))]

                if re.match(r"^●+$", current_value):
                    success = len(current_value) == len(str(value).strip())
                elif ignore_case:
                    success = current_value.lower() == main_value.lower()
                else:
                    success = current_value == main_value
            except:
                continue

        if not success:
            self.log_error(f"Could not input value {value} in field {field}")

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
                    Id = self.SetScrap('', 'div', '', 'setGrid')
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
                        self.click(element_table)
        # Neste momento devo limpar a lista gridcpousr, pois ja utilizei os seus dados.
        self.gridcpousr = []
        return True

    def SetTable(self):
        '''
        Método que retorna a table corrente
        '''
        print('time.sleep(1)')
        time.sleep(1)#tempo de espera para cada verificação.
        struct_tables = []

        content = self.driver.page_source
        soup = BeautifulSoup(content,"html.parser")
        soup = soup.select(".tmodaldialog")
        soup = self.zindex_sort(soup,True)[0] # Select a last modaldialog

        grids = soup.find_all('div', class_=(['tgetdados','tgrid','tcbrowse']))

        if grids:
            if len(grids) > 1:
                grids = self.filter_displayed_elements(grids,False)
            else:
                grids = self.filter_displayed_elements(grids,True)

            self.current_tables = grids

            for grid in grids:
                if grid:
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

                    struct_tables.append(rows)
                    rows = []
            return struct_tables

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

                if not self.SearchStack('CheckResult') and searchMsg:
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

        #lista = self.zindex_sort(lista,True)

        for line in lista:
            try:#faço uma tentativa pois caso não esteja verificando o mesmo nivel pode dar erro.
                if line.string:
                    text = line.string
                else:
                     text = line.text
                if (text[0:len(seek)] == seek) and (line.attrs['class'][0] == 'tbutton' or line.attrs['class'][0] == 'tbrowsebutton' or line.attrs['class'][0] == 'tsbutton') and line.attrs['id'] not in self.LastId and not args1 == 'setGrid':#TODO VERIFICAR SE TERÝ EFEITO USAR O LEN EM line.string
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

        lista = self.zindex_sort(lista,True)

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
                            elif line.next_sibling.text.strip() == seek.strip():
                                RetId = line.attrs['id']
                                self.classe = line.attrs['class'][0]
                                break
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

    def SearchBrowse(self, chave, descricao=None, identificador=None):
        '''
        Mètodo que pesquisa o registro no browse com base no indice informado.
        '''
        self.savebtn = ''
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
        self.wait_element_timeout(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR)
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
        self.wait_element(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(search_elements[0]))))
        self.set_element_focus(sel_browse_key())
        self.js_click(sel_browse_key())
        #sel_browse_key().click()


        soup = self.get_current_DOM()
        tradiobuttonitens = soup.select(".tradiobuttonitem")
        tradio_index = 0

        if key:
            tradiobutton_texts = list(map(lambda x: x.text[0:-3].strip() if re.match(r"\.\.\.$", x.text) else x.text.strip(), tradiobuttonitens))
            tradiobutton_text = next(iter(list(filter(lambda x: x in key, tradiobutton_texts))))
            if tradiobutton_text:
                tradio_index = tradiobutton_texts.index(tradiobutton_text)

        tradiobuttonitem = tradiobuttonitens[tradio_index]
        trb_input = next(iter(tradiobuttonitem.select("input")), None)
        if trb_input:
            sel_input = lambda: self.driver.find_element_by_xpath(xpath_soup(trb_input))
            self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(trb_input))))
            self.click(sel_input())
        else:
            self.log_error("Couldn't find key input.")

    def fill_search_browse(self, term, search_elements):
        '''
        [Internal]
        Fills search input method and presses the search button.
        '''
        sel_browse_input = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[1]))
        sel_browse_icon = lambda: self.driver.find_element_by_xpath(xpath_soup(search_elements[2]))

        current_value = self.get_element_value(sel_browse_input())

        while (current_value.rstrip() != term.strip()):
            self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(search_elements[2]))))
            self.click(sel_browse_input())
            sel_browse_input().clear()
            self.set_element_focus(sel_browse_input())
            sel_browse_input().send_keys(term.strip())
            current_value = self.get_element_value(sel_browse_input())
        self.send_keys(sel_browse_input(), Keys.ENTER)

        self.double_click(sel_browse_icon())
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

    def ProgramaInicial(self, initial_program="", environment=""):

        if initial_program:
            self.initial_program = initial_program

        self.wait_element(term='#inputStartProg', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        self.wait_element(term='#inputEnv', scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        soup = self.get_current_DOM()

        start_prog_element = next(iter(soup.select("#inputStartProg")), None)
        if start_prog_element is None:
            self.log_error("Couldn't find Initial Program input element.")
        start_prog = lambda: self.driver.find_element_by_xpath(xpath_soup(start_prog_element))
        start_prog().clear()
        self.send_keys(start_prog(), self.initial_program)

        env_element = next(iter(soup.select("#inputEnv")), None)
        if env_element is None:
            self.log_error("Couldn't find Environment input element.")
        env = lambda: self.driver.find_element_by_xpath(xpath_soup(env_element))
        env().clear()
        self.send_keys(env(), self.config.environment)

        button = self.driver.find_element(By.CSS_SELECTOR, ".button-ok")
        self.click(button)

    def Usuario(self):
        """
        Preenchimento da tela de usuario
        """
        self.wait_element(term="[name='cGetUser']", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container='body')
        current_textarea_value = ""
        initial_pos = 0
        loop_control = True
        while(loop_control):
            soup = self.get_current_DOM()

            user_element = next(iter(soup.select("[name='cGetUser']")), None)
            if user_element is None:
                self.log_error("Couldn't find User input element.")

            user = lambda: self.driver.find_element_by_xpath(xpath_soup(user_element))
            self.double_click(user())
            self.send_keys(user(), Keys.HOME)
            self.send_keys(user(), self.config.user)

            password_element = next(iter(soup.select("[name='cGetPsw']")), None)
            if password_element is None:
                self.log_error("Couldn't find User input element.")

            password = lambda: self.driver.find_element_by_xpath(xpath_soup(password_element))
            self.double_click(password())
            self.send_keys(password(), Keys.HOME)
            self.send_keys(password(), self.config.password)

            button_element = next(iter(list(filter(lambda x: self.language.enter in x.text, soup.select("button")))), None)
            if button_element is None:
                self.log_error("Couldn't find Enter button.")

            button = lambda: self.driver.find_element_by_xpath(xpath_soup(button_element))
            self.click(button())
            time.sleep(2)
            self.wait_element(term="Login", scrap_type=enum.ScrapType.MIXED, optional_term=".tsay label", position=initial_pos, main_container="body")

            initial_pos += 1
            script = f" element_list = document.querySelectorAll('textarea'); return element_list[element_list.length - 1].value.indexOf('{self.language.messages.user_not_authenticated}') != -1;"
            new_textarea_value = str(self.driver.execute_script("element_list = document.querySelectorAll('textarea'); return element_list[element_list.length - 1].value"))

            while(current_textarea_value == new_textarea_value):
                new_textarea_value = str(self.driver.execute_script("element_list = document.querySelectorAll('textarea'); return element_list[element_list.length - 1].value"))

            loop_control = self.element_exists(term=script, scrap_type=enum.ScrapType.SCRIPT)

            current_textarea_value = new_textarea_value

        self.wait_element(term=self.language.user, scrap_type=enum.ScrapType.MIXED, presence=False, optional_term="input", main_container="body")

    def Ambiente(self, change_env=False):
        """
        Preenche a tela de data base do sistema
        """

        if change_env:
            label = self.language.confirm
            container = None
        else:
            label = self.language.enter
            container = ".twindow"

        self.wait_element(self.language.database, main_container=container)
        self.wait_element(self.language.group, main_container=container)
        self.wait_element(self.language.branch, main_container=container)
        self.wait_element(self.language.environment, main_container=container)

        base_date = next(iter(self.web_scrap(self.language.database, label=True, main_container=container)), None)
        if base_date is None:
            self.log_error("Couldn't find Date input element.")
        date = lambda: self.driver.find_element_by_xpath(xpath_soup(base_date))
        self.double_click(date())
        self.send_keys(date(), Keys.HOME)
        self.send_keys(date(), self.config.date)

        group_element = next(iter(self.web_scrap(self.language.group, label=True, main_container=container)), None)
        if group_element is None:
            self.log_error("Couldn't find Group input element.")
        group = lambda: self.driver.find_element_by_xpath(xpath_soup(group_element))
        self.double_click(group())
        self.send_keys(group(), Keys.HOME)
        self.send_keys(group(), self.config.group)

        branch_element = next(iter(self.web_scrap(self.language.branch, label=True, main_container=container)), None)
        if branch_element is None:
            self.log_error("Couldn't find Branch input element.")
        branch = lambda: self.driver.find_element_by_xpath(xpath_soup(branch_element))
        self.double_click(branch())
        self.send_keys(branch(), Keys.HOME)
        self.send_keys(branch(), self.config.branch)

        environment_element = next(iter(self.web_scrap(self.language.environment, label=True, main_container=container)), None)
        if environment_element is None:
            self.log_error("Couldn't find Module input element.")
        env = lambda: self.driver.find_element_by_xpath(xpath_soup(environment_element))
        if ("disabled" not in environment_element.attrs["class"] and env().is_enabled()):
            self.double_click(env())
            self.send_keys(env(), Keys.HOME)
            self.send_keys(env(), self.config.module)

        buttons = self.filter_displayed_elements(self.web_scrap(label, scrap_type=enum.ScrapType.MIXED, optional_term="button", main_container=container), True)
        button_element = next(iter(buttons), None)
        if button_element is None:
            self.log_error(f"Couldn't find {label} button.")
        button = lambda: self.driver.find_element_by_xpath(xpath_soup(button_element))
        self.click(button())

        self.wait_element(term=self.language.database, scrap_type=enum.ScrapType.MIXED, presence=False, optional_term="input", main_container=container)

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
            self.config.language = self.get_language()
            self.language = LanguagePack(self.config.language)

        if not self.backupSetup:
            self.backupSetup = { 'progini': self.config.initialprog, 'data': self.config.date, 'grupo': self.config.group, 'filial': self.config.branch }
        if not self.config.skip_environment:
            self.ProgramaInicial(initial_program)

        self.Usuario()
        self.Ambiente()

        while(not self.element_exists(term=".tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")):
            self.close_modal()


        self.set_log_info()

    def Program(self, rotina):
        """
        Preenche a tela de rotina
        """
        self.config.routine = rotina
        self.log.program = rotina
        self.set_program(rotina)

    def SetValue(self, campo, valor, grid=False, grid_number=1, disabled=False, ignore_case=True):
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
                self.input_value(campo, valor, ignore_case)
                #self.set_enchoice(campo, valor, '', 'Enchoice', '', '', disabled)
        else:
            self.input_grid_appender(campo, valor, grid_number - 1)

    def LogOff(self):
        """
        Efetua logOff do sistema
        """
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('q').key_up(Keys.CONTROL).perform()
        self.SetButton(self.language.finish)

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
            path = os.path.join(os.path.dirname(__file__), r'core\\data\\sx3.csv')
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

            valsub = self.remove_mask(valor)
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
                            self.send_keys(element(), Keys.ENTER)#element.send_keys(Keys.ENTER)
                            print('time.sleep(1) - 1506')
                            time.sleep(1)
                            self.send_keys(element(), valsub)#element.send_keys(valor)
                            self.send_keys(element(), Keys.ENTER)#element.send_keys(Keys.ENTER)

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
                        #self.double_click(element())#self.send_keys(element, Keys.ENTER)
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
                            element_ = self.driver.find_element_by_id(Id)
                            self.lenvalorweb = len(self.get_web_value(element_))

                            if element_.tag_name == 'div':
                                element_ = element_.find_element_by_tag_name("input")

                            print('time.sleep(1) - 1541')
                            time.sleep(1)
                            self.click(element_)
                            if valsub != valor and self.check_mask(element_):
                                self.send_keys(element_, valsub)
                            else:
                                self.send_keys(element_, valor)
                            if len(valor) < self.lenvalorweb:
                                self.send_keys(element_, Keys.ENTER)
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
        if args1 != 'input':
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
        if cabitem != 'aItens':
            if Id:
                # print('time.sleep(1) - 1578')
                # time.sleep(1)
                element = self.driver.find_element_by_id(Id)
                if args1 != 'input':
                    self.click(element)
                # print('time.sleep(1) - 1583')
                # time.sleep(1)
                valorweb = self.get_web_value(element)
                self.lenvalorweb = len(valorweb)
                valorweb = valorweb.strip()
                if self.consolelog and valorweb != '':
                    print(valorweb)
                if self.check_mask(element):
                    valorweb = self.remove_mask(valorweb)
                    valorusr = self.remove_mask(valorusr)
                if type(valorweb) is str:
                    valorweb = valorweb[0:len(str(valorusr))]
                # print('time.sleep(1) - 1595')
                # time.sleep(1)
            if args1 != 'input':
                self.LogResult(campo, valorusr, valorweb)
        else:
            self.check_grid_appender(line - 1, campo, valorusr, grid_number - 1)
            self.rota = 'CheckResultItens'

        return valorweb

    def get_web_value(self, element):
        """
        Coleta as informações do campo baseado no ID
        """

        if element.tag_name == "div":
            element_children = element.find_element(By.CSS_SELECTOR, "div > * ")
            if element_children is not None:
                element = element_children

        if element.tag_name == "label":
            web_value = element.get_attribute("text")
        elif element.tag_name == "select":
            current_select = int(element.get_attribute('value'))
            selected_element = element.find_elements(By.CSS_SELECTOR, "option")[current_select]
            web_value = selected_element.text
        else:
            web_value = element.get_attribute("value")

        return web_value

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

        self.compare_field_values(field, user_value, captured_value, message)

    def ChangeEnvironment(self):
        """
        clique na area de troca de ambiente do protheus
        """
        Id = self.SetScrap('ChangeEnvironment','div','tbutton')
        if Id:
            element = self.driver.find_element_by_id(Id)
            self.click(element)
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

        while(not self.element_exists(term=".tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR)):
            self.close_modal()

        self.set_program(self.config.routine)

    def GetFunction(self):
        stack = inspect.stack()
        function_name = "screenshot"
        for line in stack:
            if self.config.routine in line.filename:
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
                    self.SetButton(self.language.details)
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
        self.SetButton(self.language.close)
        self.savebtn = ''

        close_element = self.get_closing_button(is_advpl)

        self.click(close_element)
        if not is_advpl:
            self.SetButton(self.language.leave_page)
        self.log.new_line(False, message)
        self.log.save_file()
        self.assertTrue(False, message)

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

    def element_exists(self, term, scrap_type=enum.ScrapType.TEXT, position=0, optional_term="", main_container=".tmodaldialog,.ui-dialog"):
        '''
        [Internal]

        Returns a boolean if element exists on the screen.

        :param term: The first term to use on a search of element
        :type term: str
        :param scrap_type: Type of element search
        :type scrap_type: enum.ScrapType
        :param position: Position which element is located
        :type position: int
        :param optional_term: Second term to use on a search of element. Used in MIXED search
        :type optional_term: str
        :default scrap_type: enum.ScrapType.TEXT
        :default position: 0
        :default optional_term: ""

        :return: True if element is present. False if element is not present.
        :rtype: bool

        Usage:

        >>> element_is_present = element_exists(term=".ui-dialog", scrap_type=enum.ScrapType.CSS_SELECTOR)
        >>> element_is_present = element_exists(term=".tmodaldialog.twidget", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1)
        >>> element_is_present = element_exists(term=text, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay")
        '''
        if self.consolelog:
            print(f"term={term}, scrap_type={scrap_type}, position={position}, optional_term={optional_term}")

        if scrap_type == enum.ScrapType.SCRIPT:
            return bool(self.driver.execute_script(term))
        elif (scrap_type != enum.ScrapType.MIXED and not (scrap_type == enum.ScrapType.TEXT and not re.match(r"\w+(_)", term))):
            selector = term
            if scrap_type == enum.ScrapType.CSS_SELECTOR:
                by = By.CSS_SELECTOR
            elif scrap_type == enum.ScrapType.XPATH:
                by = By.XPATH
            elif scrap_type == enum.ScrapType.TEXT:
                by = By.CSS_SELECTOR
                selector = f"[name*='{term}']"

            if scrap_type != enum.ScrapType.XPATH:
                soup = self.get_current_DOM()
                container_selector = self.base_container
                if (main_container is not None):
                    container_selector = main_container
                containers = self.zindex_sort(soup.select(container_selector), reverse=True)
                container = next(iter(containers), None)
                if not container:
                    return False

                try:
                    container_element = self.driver.find_element_by_xpath(xpath_soup(container))
                except:
                    return False
            else:
                container_element = self.driver

            element_list = container_element.find_elements(by, selector)
        else:
            if scrap_type == enum.ScrapType.MIXED:
                selector = optional_term
            else:
                selector = "div"

            element_list = self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container)
        if position == 0:
            return len(element_list) > 0
        else:
            return len(element_list) >= position

    def SetLateralMenu(self, menuitens):
        '''
        [External]
        Navigates through the lateral menu using provided menu path.
        e.g. "MenuItem1 > MenuItem2 > MenuItem3"
        '''
        # try:
        self.wait_element(term=".tmenu", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body")
        menuitens = list(map(str.strip, menuitens.split(">")))

        soup = self.get_current_DOM()

        menuXpath = soup.select(".tmenu")

        menu = menuXpath[0]
        child = menu
        count = 0
        for menuitem in menuitens:
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".tmenu")))
            self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".tmenu .tmenuitem")))
            self.wait_element(term=menuitem, scrap_type=enum.ScrapType.MIXED, optional_term=".tmenuitem", main_container="body")
            subMenuElements = menu.select(".tmenuitem")
            endTime =   time.time() + 90
            while not subMenuElements or len(subMenuElements) < self.children_element_count(f"#{child.attrs['id']}", ".tmenuitem"):
                menu = self.get_current_DOM().select(f"#{child.attrs['id']}")[0]
                subMenuElements = menu.select(".tmenuitem")
                if time.time() > endTime and (not subMenuElements or len(subMenuElements) < self.children_element_count(".tmenu", ".tmenuitem")):
                    self.log_error(f"Couldn't find menu item: {menuitem}")
            submenu = ""
            child = list(filter(lambda x: x.text.startswith(menuitem), subMenuElements))[0]
            submenu = lambda: self.driver.find_element_by_xpath(xpath_soup(child))
            if subMenuElements and submenu():
                self.scroll_to_element(submenu())
                ActionChains(self.driver).move_to_element(submenu()).click().perform()
                if count < len(menuitens) - 1:
                    self.wait_element(term=menuitens[count], scrap_type=enum.ScrapType.MIXED, optional_term=".tmenuitem", main_container="body")
                    menu = self.get_current_DOM().select(f"#{child.attrs['id']}")[0]
            else:
                self.log_error(f"Error - Menu Item does not exist: {menuitem}")
            count+=1
        # except Exception as error:
        #     print(str(error))
        #     print("SetLateralMenu failed!")
        #     print("Trying again!")
        #     self.SetLateralMenu(menuitens)

    def GetValue(self, field, grid=False, line=1, grid_number=1):
        '''
        Get a web value from DOM elements
        '''
        if not grid:
            if re.match(r"\w+(_)", field):
                element = next(iter(self.web_scrap(f"[name*='{field}']", scrap_type=enum.ScrapType.CSS_SELECTOR)), None)
            else:
                element = next(iter(self.web_scrap(field, scrap_type=enum.ScrapType.TEXT, label=True)), None)

            selenium_element = lambda: self.driver.find_element_by_xpath(xpath_soup(element))

            value = self.get_web_value(selenium_element())
        else:
            field_array = [line-1, field, "", grid_number-1]
            x3_dictionaries = self.create_x3_tuple()
            value = self.check_grid(field_array, x3_dictionaries, get_value=True)

        return value

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

    def SetButton(self, button, sub_item=""):
        '''
        Method that clicks on a button of the interface.
        '''
        try:
            soup_element  = ""
            if (button.lower() == "x"):
                self.wait_element(term=".ui-button.ui-dialog-titlebar-close[title='Close']", scrap_type=enum.ScrapType.CSS_SELECTOR)
            else:
                self.wait_element_timeout(term=button, scrap_type=enum.ScrapType.MIXED, optional_term="button", timeout=10, step=0.1)

            layers = 0
            if button == self.language.confirm:
                layers = len(self.driver.find_elements(By.CSS_SELECTOR, ".tmodaldialog"))

            success = False
            endtime = time.time() + 10
            while(time.time() < endtime and not soup_element):
                soup_objects = self.web_scrap(term=button, scrap_type=enum.ScrapType.MIXED, optional_term="button")

                if soup_objects:
                    soup_element = lambda : self.driver.find_element_by_xpath(xpath_soup(soup_objects[0]))

            if (button.lower() == "x" and self.element_exists(term=".ui-button.ui-dialog-titlebar-close[title='Close']", scrap_type=enum.ScrapType.CSS_SELECTOR)):
                element = self.driver.find_element(By.CSS_SELECTOR, ".ui-button.ui-dialog-titlebar-close[title='Close']")
                self.scroll_to_element(element)
                time.sleep(2)
                self.click(element)

            if not soup_element:
                soup_objects = self.web_scrap(term=self.language.other_actions, scrap_type=enum.ScrapType.MIXED, optional_term="button")

                if soup_objects:
                    soup_element = lambda : self.driver.find_element_by_xpath(xpath_soup(soup_objects[0]))
                else:
                    self.log_error("Couldn't find element")

                self.scroll_to_element(soup_element())#posiciona o scroll baseado na height do elemento a ser clicado.
                self.click(soup_element())

                success = self.click_sub_menu(button if button.lower() != self.language.other_actions.lower() else sub_item)
                if success:
                    return

            if soup_element:
                if button in self.language.no_actions:
                    self.idwizard = []
                    self.LastIdBtn = []
                else:
                    self.savebtn = button

                self.scroll_to_element(soup_element())#posiciona o scroll baseado na height do elemento a ser clicado.
                self.click(soup_element())

            # if button != self.language.other_actions:

            if sub_item:
                soup_objects = self.web_scrap(term=sub_item, scrap_type=enum.ScrapType.MIXED, optional_term=".tmenupopupitem", main_container="body")

                if soup_objects:
                    soup_element = lambda : self.driver.find_element_by_xpath(xpath_soup(soup_objects[0]))
                else:
                    self.log_error("Couldn't find element")

                self.click(soup_element())

            if button == self.language.save and soup_objects[0].parent.attrs["id"] in self.get_enchoice_button_ids(layers):
                self.wait_element(term="", scrap_type=enum.ScrapType.MIXED, optional_term="[style*='fwskin_seekbar_ico']")
                self.wait_element(term="", scrap_type=enum.ScrapType.MIXED, presence=False, optional_term="[style*='fwskin_seekbar_ico']")

            elif button == self.language.confirm and soup_objects[0].parent.attrs["id"] in self.get_enchoice_button_ids(layers):
                self.wait_element(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=layers + 1, main_container="body")

            if button == self.language.edit or button == self.language.view or button == self.language.delete or button == self.language.add:
                if not self.element_exists(term=".ui-dialog", scrap_type=enum.ScrapType.CSS_SELECTOR):
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
            self.click(item)
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
        self.wait_element(term="[style*='fwskin_seekbar_ico']", scrap_type=enum.ScrapType.CSS_SELECTOR, position=2, main_container="body")
        Ret = self.fill_search_browse(branch, self.get_search_browse_elements())
        if Ret:
            #self.SetButton('OK','','',60,'div','tbutton')
            self.SetButton('OK')

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
            self.click(element)
            self.send_keys(element, tabela)
            self.send_keys(element, Keys.ENTER)
            #self.SetButton('Ok','','',60,'div','tsbutton')
            self.SetButton("Ok")
        except:
            if self.consolelog:
                print("Não encontrou o campo Pesquisar")

    def ClickFolder(self, item):
        '''
        Método que efetua o clique na aba
        '''
        self.wait_element(term=item, scrap_type=enum.ScrapType.MIXED, optional_term=".tfolder.twidget")

        if self.savebtn == self.language.view:
            self.rota == 'CheckResultItens'
        else:
            self.rota = "ClickFolder"

        if self.VldData():
            self.wait_element(term=item, scrap_type=enum.ScrapType.MIXED, optional_term=".button-bar a")
            #Retira o ToolTip dos elementos focados.
            self.move_to_element(self.driver.find_element_by_tag_name("html"))

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
                self.set_element_focus(element())
                time.sleep(1)
                self.driver.execute_script("arguments[0].click()", element())
            else:
                self.log_error("Couldn't find panel item.")

    def ClickBox(self, fields, contents_list, browse_index=1 ):
        '''
        Method that clicks in checkbox
        '''
        time.sleep(3)
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
                self.click(element)
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
                            self.click(elements_list[index])
                            if class_grid != 'tcbrowse':
                                print('time.sleep(1)')
                                time.sleep(1)
                                self.double_click(elements_list[index])
                                print('time.sleep(2)')
                                time.sleep(1)
                            else:
                                self.send_keys(elements_list[index], Keys.ENTER)
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
        self.Program(self.config.routine)

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
        if modals and self.element_exists(term=".tmodaldialog .tbrowsebutton", scrap_type=enum.ScrapType.CSS_SELECTOR, main_container="body"):
            buttons = modals[0].select(".tbrowsebutton")
            if buttons:
                close_button = next(iter(list(filter(lambda x: x.text == self.language.close, buttons))))
                time.sleep(0.5)
                selenium_close_button = lambda: self.driver.find_element_by_xpath(xpath_soup(close_button))
                if close_button:
                    try:
                        self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath_soup(close_button))))
                        self.click(selenium_close_button())
                    except:
                        pass

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

    def remove_mask(self, string):
        """
        Removes special characters from received string.
        """
        caracter = (r'[.\/-]')
        if string[0:4] != 'http':
            match = re.search(caracter, string)
            if match:
                string = re.sub(caracter, '', string)

        return string

    def SetKey(self, key, grid=False, grid_number=1):
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
        grid_number-=1
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
                    self.set_element_focus(element)
                    self.send_keys(element, supported_keys[key.upper()])
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
        self.set_element_focus(element)

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
            if line.is_displayed() and ((line.get_attribute('name') != None and line.get_attribute('name').split('->')[1] == campo) or  line.text.strip() == campo.strip()):
                checked = "CHECKED" in line.get_attribute('class').upper()
                if valor != checked:
                    element = line
                    self.click(line)
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
                        self.click(line2)
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
        return self.element_exists(term=self.language.cancel, scrap_type=enum.ScrapType.MIXED, optional_term="div.tbrowsebutton")

    def clear_grid(self):
        self.btnenchoice = True
        self.grid_input = []
        self.grid_check = []

    def input_grid_appender(self, column, value, grid_number=0, new=False):
        self.grid_input.append([column, value, grid_number, new])

    def check_grid_appender(self, line, column, value, grid_number=0):
        self.grid_check.append([line, column, value, grid_number])

    def LoadGrid(self):
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

    def create_x3_tuple(self):
        x3_dictionaries = ()
        inputs = list(map(lambda x: x[0], self.grid_input))
        checks = list(map(lambda x: x[1], self.grid_check))
        fields = list(filter(lambda x: "_" in x, inputs + checks))
        if fields:
            x3_dictionaries = self.get_x3_dictionaries(fields)
        return x3_dictionaries

    def fill_grid(self, field, x3_dictionaries, initial_layer):
        field_to_label = {}
        field_to_valtype = {}
        field_to_len = {}

        if x3_dictionaries:
            field_to_label = x3_dictionaries[2]
            field_to_valtype = x3_dictionaries[0]
            field_to_len = x3_dictionaries[1]

        while(self.element_exists(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, main_container="body")):
            print("Waiting for container to be active")
            time.sleep(1)

        soup = self.get_current_DOM()

        containers = soup.select(".tmodaldialog")
        if containers:
            containers = self.zindex_sort(containers, True)

            grids = containers[0].select(".tgetdados")
            if not grids:
                grids = containers[0].select(".tgrid")

            grids = self.filter_displayed_elements(grids)
            if grids:
                headers = self.get_headers_from_grids(grids)
                grid_id = grids[field[2]].attrs["id"]
                if grid_id not in self.grid_counters:
                    self.grid_counters[grid_id] = 0

                column_name = ""
                if field[2] > len(grids):
                    self.log_error(self.language.messages.grid_number_error)

                row = self.get_selected_row(grids[field[2]].select("tbody tr"))
                if row:
                    while int(row.attrs["id"]) < self.grid_counters[grid_id]:
                        self.new_grid_line(field, False)
                        row = self.get_selected_row(self.get_current_DOM().select(f"#{grid_id} tbody tr"))

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
                        xpath = xpath_soup(columns[column_number])

                        try_counter = 0

                        while(current_value.strip() != field[1].strip()):

                            selenium_column = lambda: self.get_selenium_column_element(xpath) if self.get_selenium_column_element(xpath) else self.try_recover_lost_line(field, grid_id, row, headers, field_to_label)
                            self.scroll_to_element(selenium_column())
                            self.js_click(selenium_column())
                            self.set_element_focus(selenium_column())

                            while(not self.element_exists(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, main_container="body")):
                                time.sleep(1)
                                self.scroll_to_element(selenium_column())
                                self.set_element_focus(selenium_column())
                                self.js_click(selenium_column())
                                ActionChains(self.driver).move_to_element(selenium_column()).send_keys_to_element(selenium_column(), Keys.ENTER).perform()
                                time.sleep(1)

                            self.wait_element(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, main_container="body")
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
                                    user_value = self.remove_mask(user_value)

                                self.wait.until(EC.visibility_of(selenium_input()))
                                self.set_element_focus(selenium_input())
                                self.js_click(selenium_input())
                                self.try_send_keys(selenium_input, user_value, try_counter)

                                if try_counter < 2:
                                    try_counter += 1
                                else:
                                    try_counter = 0
                                # time.sleep(1)
                                # if last_column != column_number:
                                #     ActionChains(self.driver).move_to_element(selenium_input()).send_keys_to_element(selenium_input(), user_value).perform()
                                # else:
                                #     selenium_input().send_keys(user_value)

                                # last_column = column_number

                                if (("_" in field[0] and field_to_len != {} and int(field_to_len[field[0]]) > len(field[1])) or lenfield > len(field[1])):
                                    if (("_" in field[0] and field_to_valtype != {} and field_to_valtype[field[0]] != "N") or valtype != "N"):
                                        self.send_keys(selenium_input(), Keys.ENTER)
                                    else:
                                        if not (re.match(r"[0-9]+,[0-9]+", user_value)):
                                            self.send_keys(selenium_input(), Keys.ENTER)
                                        else:
                                            self.wait_element_timeout(term= ".tmodaldialog.twidget", scrap_type= enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, presence=False, main_container="body")
                                            if self.element_exists(term=".tmodaldialog.twidget", scrap_type=enum.ScrapType.CSS_SELECTOR, position=initial_layer+1, main_container="body"):
                                                self.send_keys(selenium_input(), Keys.ENTER)

                                self.wait_element(term=xpath_soup(child[0]), scrap_type=enum.ScrapType.XPATH, presence=False)
                                time.sleep(1)
                                current_value = self.get_element_text(selenium_column())

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
                                    self.send_keys(self.driver.find_element_by_xpath(xpath_soup(child[0])), Keys.ENTER)
                                    current_value = field[1]
                    else:
                        self.log_error("Couldn't find columns.")
                else:
                    self.log_error("Couldn't find rows.")
            else:
                self.log_error("Couldn't find grids.")

    def get_selenium_column_element(self, xpath):
        '''
        [Internal]
        Workaround method to be used instead of a lambda function on fill_grid method.
        '''
        try:
            return self.driver.find_element_by_xpath(xpath)
        except:
            return False

    def try_recover_lost_line(self, field, grid_id, row, headers, field_to_label):
        '''
        [Internal]
        Workaround method to keep trying to get the right row fill_grid method.
        '''
        print("Recovering lost line")
        while int(row.attrs["id"]) < self.grid_counters[grid_id]:
            self.new_grid_line(field, False)
            row = self.get_selected_row(self.get_current_DOM().select(f"#{grid_id} tbody tr"))

        columns = row.select("td")
        if columns:
            if "_" in field[0]:
                column_name = field_to_label[field[0]]
            else:
                column_name = field[0]

            if column_name not in headers[field[2]]:
                self.log_error(self.language.messages.grid_column_error)

            column_number = headers[field[2]][column_name]
            xpath = xpath_soup(columns[column_number])
            ret = self.get_selenium_column_element(xpath)
            while not ret:
                ret = self.try_recover_lost_line(field, grid_id, row, headers, field_to_label)
            return ret
        else:
            return False

    def check_grid(self, field, x3_dictionaries, get_value=False):
        field_to_label = {}
        if x3_dictionaries:
            field_to_label = x3_dictionaries[2]

        while(self.element_exists(term=".tmodaldialog", scrap_type=enum.ScrapType.CSS_SELECTOR, position=3, main_container="body")):
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

                        if get_value:
                            return text

                        field_name = f"({field[0]}, {column_name})"
                        self.LogResult(field_name, field[2], text)
                    else:
                        self.log_error("Couldn't find columns.")
                else:
                    self.log_error("Couldn't find rows.")
            else:
                self.log_error("Couldn't find grids.")

    def new_grid_line(self, field, addGridLineCounter=True):
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
                        self.set_element_focus(second_column())
                        self.wait.until(EC.visibility_of_element_located((By.XPATH, xpath_soup(columns[0]))))
                        ActionChains(self.driver).move_to_element(second_column()).send_keys_to_element(second_column(), Keys.DOWN).perform()

                        while not(self.element_exists(term=f"{grid_selector} tbody tr", scrap_type=enum.ScrapType.CSS_SELECTOR, position=len(rows)+1)):
                            print("Waiting for the new line to show")
                            time.sleep(1)

                        if (addGridLineCounter):
                            self.add_grid_row_counter(grids[field[2]])
                    else:
                        self.log_error("Couldn't find columns.")
                else:
                    self.log_error("Couldn't find rows.")
            else:
                self.log_error("Couldn't find grids.")

    def get_x3_dictionaries(self, fields):

        prefixes = list(set(map(lambda x:x.split("_")[0] + "_" if "_" in x else "", fields)))
        regex = self.generate_regex_by_prefixes(prefixes)

        #caminho do arquivo csv(SX3)
        path = os.path.join(os.path.dirname(__file__), r'core\\data\\sx3.csv')
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

    def get_headers_from_grids(self, grids):
        headers = []
        for item in grids:
            labels = item.select("thead tr label")
            keys = list(map(lambda x: x.text.strip(), labels))
            values = list(map(lambda x: x[0], enumerate(labels)))
            headers.append(dict(zip(keys, values)))
        return headers

    def js_click(self, element):
        self.driver.execute_script("arguments[0].click()", element)

    def wait_element(self, term, scrap_type=enum.ScrapType.TEXT, presence=True, position=0, optional_term=None, main_container=".tmodaldialog,.ui-dialog"):
        endtime = time.time() + 10
        if self.consolelog:
            print("Waiting...")
        if presence:
            while not self.element_exists(term, scrap_type, position, optional_term, main_container):
                print('time.sleep(0.1) 2901')
                time.sleep(0.1)
        else:
            while self.element_exists(term, scrap_type, position, optional_term, main_container):
                print('time.sleep(0.1) 2905')
                time.sleep(0.1)

        if presence:
            print("Element found! Waiting for element to be displayed.")
            element = next(iter(self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container)), None)
            if element is not None:
                sel_element = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
                while(not sel_element().is_displayed() and time.time() < endtime):
                    time.sleep(0.1)

    def wait_element_timeout(self, term, scrap_type=enum.ScrapType.TEXT, timeout=5.0, step=0.1, presence=True, position=0, optional_term=None, main_container=".tmodaldialog,.ui-dialog"):
        success = False
        if presence:
            endtime = time.time() + timeout
            while time.time() < endtime:
                time.sleep(step)
                if self.element_exists(term, scrap_type, position, optional_term, main_container):
                    success = True
                    break
        else:
            endtime = time.time() + timeout
            while time.time() < endtime:
                time.sleep(step)
                if not self.element_exists(term, scrap_type, position, optional_term, main_container):
                    success = True
                    break

        if presence and success:
            print("Element found! Waiting for element to be displayed.")
            element = next(iter(self.web_scrap(term=term, scrap_type=scrap_type, optional_term=optional_term, main_container=main_container)), None)
            if element is not None:
                sel_element = lambda: self.driver.find_element_by_xpath(xpath_soup(element))
                while(not sel_element().is_displayed()):
                    time.sleep(0.1)

    def get_selected_row(self, rows):
        filtered_rows = list(filter(lambda x: len(x.select("td.selected-cell")), rows))
        if filtered_rows:
            return next(iter(filtered_rows))

    def SetFilePath(self,value):
        self.wait_element("Nome do Arquivo:")
        element = self.driver.find_element(By.CSS_SELECTOR, ".filepath input")
        if element:
            self.driver.execute_script("document.querySelector('#{}').value='';".format(element.get_attribute("id")))
            self.send_keys(element, value)
        elements = self.driver.find_elements(By.CSS_SELECTOR, ".tremoteopensave button")
        if elements:
            for line in elements:
                if line.text.strip().upper() == "ABRIR":
                    self.click(line)
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
                self.click(selenium_button)

    def get_enchoice_button_ids(self, layer):
        try:
            soup = self.get_current_DOM()
            current_layer = self.zindex_sort(soup.select(".tmodaldialog"), False)[layer - 1]
            buttons = list(filter(lambda x: x.text.strip() != "", current_layer.select(".tpanel button")))
            return list(map(lambda x: x.parent.attrs["id"], buttons))
        except Exception as error:
            if self.consolelog:
                print(error)
                return []

    def CheckView(self, text, element_type="help"):
        '''
        Checks if a certain text is present in the screen at the time.
        '''
        if element_type == "help":
            self.wait_element_timeout(term=text, scrap_type=enum.ScrapType.MIXED, timeout=2.5, step=0.5, optional_term=".tsay")
            if not self.element_exists(term=text, scrap_type=enum.ScrapType.MIXED, optional_term=".tsay"):
                self.errors.append(self.language.messages.text_not_found)
            else:
                self.SetButton(self.language.close)

    def get_language(self):
        '''
        [Internal]
        [returns String]
        Gets the current language of the html.
        '''
        language = self.driver.find_element(By.CSS_SELECTOR, "html").get_attribute("lang")
        if self.consolelog:
            print(language)
        return language

    def add_grid_row_counter(self, grid):
        '''
        [Internal]
        Adds the counter of rows to the global dictionary.
        '''
        grid_id = grid.attrs["id"]

        if grid_id not in self.grid_counters:
            self.grid_counters[grid_id] = 0
        else:
            self.grid_counters[grid_id]+=1

    def children_element_count(self, element_selector, children_selector):
        '''
        [Internal]
        [returns Int]
        Returns the count of elements of a certain CSS Selector that exists within a certain element located also via CSS Selector.
        '''
        script = f"return document.querySelector('{element_selector}').querySelectorAll('{children_selector}').length;"
        return int(self.driver.execute_script(script))

    def try_send_keys(self, element_function, key, try_counter=0):
        """
        [Internal]
        Try to send value to element
        """
        self.wait.until(EC.visibility_of(element_function()))
        if try_counter == 0:
            element_function().send_keys(key)
        elif try_counter == 1:
            ActionChains(self.driver).move_to_element(element_function()).send_keys_to_element(element_function(), key).perform()
        else:
            ActionChains(self.driver).move_to_element(element_function()).send_keys(key).perform()

    def find_label_element(self, label_text, container):
        """
        [Internal]

        Find input element next to label containing the label_text parameter.

        :param label_text: The label text to be searched
        :type label_text: string
        :param container: The main container object to be used
        :type container: BeautifulSoup object

        :return: A list containing a BeautifulSoup object next to the label
        :rtype: List of BeautifulSoup objects

        Usage:

        >>> self.find_label_element("User:", container_object)
        """
        element = next(iter(list(map(lambda x: self.find_first_div_parent(x), container.find_all(text=re.compile(f"{label_text}" + r"\*?"))))), None)
        if element is None:
            return []

        #Checking previous and next element:
        next_sibling = element.find_next_sibling("div")
        second_next_sibling = next_sibling.find_next_sibling("div")

        previous_sibling = element.find_next_sibling("div")
        second_previous_sibling = previous_sibling.find_next_sibling("div")

        #If current element is tsay and next or second next element is tget or tcombobox => return tget or tcombobox
        if (hasattr(element, "attrs") and "class" in element.attrs
            and "tsay" in element.attrs["class"]
            and (hasattr(next_sibling, "attrs") and "class" in next_sibling.attrs and "id" in next_sibling.attrs
            and ("tget" in next_sibling.attrs["class"] or "tcombobox" in next_sibling.attrs["class"])
            and next_sibling.attrs["id"] not in self.used_ids)
            or (hasattr(second_next_sibling, "attrs") and "class" in second_next_sibling.attrs and "id" in second_next_sibling.attrs
            and ("tget" in second_next_sibling.attrs["class"] or "tcombobox" in second_next_sibling.attrs["class"])
            and second_next_sibling.attrs["id"] not in self.used_ids)):

            if (("tget" in next_sibling.attrs["class"]
                    or "tcombobox" in next_sibling.attrs["class"])
                    and next_sibling.attrs["id"] not in self.used_ids):
                self.used_ids.append(next_sibling.attrs["id"])
                return [next_sibling]
            elif (("tget" in second_next_sibling.attrs["class"]
                    or "tcombobox" in second_next_sibling.attrs["class"])
                    and second_next_sibling.attrs["id"] not in self.used_ids):
                self.used_ids.append(second_next_sibling.attrs["id"])
                return [second_next_sibling]
            else:
                return []

        #If current element is tsay and previous or second previous element is tget or tcombobox => return tget or tcombobox
        elif (hasattr(element, "attrs") and "class" in element.attrs
            and "tsay" in element.attrs["class"]
            and (hasattr(previous_sibling, "attrs") and "class" in previous_sibling.attrs and "id" in previous_sibling.attrs
            and ("tget" in previous_sibling.attrs["class"] or "tcombobox" in previous_sibling.attrs["class"])
            and previous_sibling.attrs["id"] not in self.used_ids)
            or (hasattr(second_previous_sibling, "attrs") and "class" in second_previous_sibling.attrs and "id" in second_previous_sibling.attrs
            and ("tget" in second_previous_sibling.attrs["class"] or "tcombobox" in second_previous_sibling.attrs["class"])
            and second_previous_sibling.attrs["id"] not in self.used_ids)):

            if (("tget" in previous_sibling.attrs["class"]
                    or "tcombobox" in previous_sibling.attrs["class"])
                    and previous_sibling.attrs["id"] not in self.used_ids):
                self.used_ids.append(previous_sibling.attrs["id"])
                return [previous_sibling]
            elif (("tget" in second_previous_sibling.attrs["class"]
                    or "tcombobox" in second_previous_sibling.attrs["class"])
                    and second_previous_sibling.attrs["id"] not in self.used_ids):
                self.used_ids.append(second_previous_sibling.attrs["id"])
                return [second_previous_sibling]
            else:
                return []

        #If element is not tsay => return it
        elif (hasattr(element, "attrs") and "class" in element.attrs
            and "tsay" not in element.attrs["class"]):
            return [element]

        #If label exists but there is no element associated with it => return empty list
        else:
            return []
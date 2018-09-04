import time
import selenium
import re
import inspect
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as AC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys  import  Keys

# Importações da classe base
# Importations from base class
from tir.technologies.core.base import Base
from tir.technologies.core.config import ConfigLoader
from tir.technologies.core import enumerations as enum
from tir.technologies.core.third_party.xpath_soup import xpath_soup

# Classe que herda os métodos da classe base
# Class that describes the methods of the base class
class ApwInternal(Base):

    def __init__(self, config_path=""):

        Base.__init__(self, config_path)
        self.config = ConfigLoader(config_path)

        self.tries = 1
        self.IdRet = ''
        self.gridValues = []
        
        # Variável importada da classe Webapp
        # Variable imported from the Webapp class
        self.lineGrid = 0

    # Funções usadas no script
    # Functions used in the script
    def CheckBrowse(self, valores):
        '''
        Verify if a value exists in the browse
        '''
        
        lstValuesGrid = valores.split("|")
        self.tries = 1
        self.wait_elements_load(lstValuesGrid, "table")

        if self.IdRet == "":
            self.log_error('Não encontrou grid com conteúdo : ' + lstValuesGrid)

    def CheckLink(self, Link):
        '''
        Method to check if a link is valid
        '''
        try:
            self.tries = 1
            self.wait_elements_load(Link, "link")
            menu = self.driver.find_elements_by_partial_link_text('%s' % Link)
            for a in menu:
                if a.tag_name == 'a' and a.text.startswith(Link):
                    linkcheck = self.driver.find_element_by_partial_link_text('%s' % Link).get_attribute('href')
                    r = requests.get(linkcheck)
                    if r.status_code != 200:
                        self.log_error(str("O arquivo não foi gerado para download"))

        except Exception as e:
            self.log_error(str(e))

    def ClickLink(self, Link):
        '''
        Method to click in a link
        '''
        try:
            self.tries = 1
            self.wait_elements_load(Link, "link")
            menu = self.driver.find_elements_by_partial_link_text('%s' % Link)

            for a in menu:
                if a.tag_name == 'a' and a.text.startswith(Link):
                    self.Click(a)

        except Exception as e:
            self.log_error(str(e))

    def ClickMenu(self, caminho):
        '''
        Method to click in a option on the menu
        '''
        lstMenus = caminho.split(">")

        for noMenu in lstMenus:

            # Retirando espaços antes e depois
            # Removing spaces before and after
            noMenu = noMenu.strip()

            self.tries = 1
            self.wait_elements_load(noMenu)

            menu = self.driver.find_elements_by_partial_link_text('%s' % noMenu)

            for a in menu:
                if a.tag_name == 'a' and a.text.startswith(noMenu):
                    try:
                        self.Click(a)
                    except Exception as e:
                        self.log_error(str(e))

    def CloseAlert(self):
        '''
        Method to close an alert
        '''
        try:
            aviso = self.wait
            aviso.until(EC.alert_is_present())

            alert = self.driver.switch_to.alert
            alert.accept()
        except TimeoutException:
            time.sleep(0.5)

    def CloseWindow(self):
        '''
		Method to close a window
		'''
        self.driver.close()

    def EndCase(self):
        '''
		Method to end the testcase
		'''

        self.driver.refresh()

    def SetButton(self, button, type=''):
        '''
        Method that clicks on a button of the interface.
        '''
        try:
            element = ''
            self.tries = 1
            if type == '':
                self.wait_elements_load(button, 'button')

                if self.IdRet == '':
                    try:
                        element = self.driver.find_element_by_xpath("//*[@value='%s']" % button)
                    except:
                        content = self.driver.page_source
                        soup = BeautifulSoup(content, "html.parser")
                        lista = soup.find_all('button')
                        for line in lista:
                            if line.text.strip().replace(" ", "").startswith(button.replace(" ", "")):
                                element = self.driver.find_element_by_name(line.name)
                else:
                    element = self.driver.find_element_by_id(self.IdRet)
            else:

                self.wait_elements_load(button, 'label')
                content = self.driver.page_source
                soup = BeautifulSoup(content, "html.parser")
                lista = soup.find_all('div')
                for line in lista:
                    if line.text.strip().replace(" ", "").startswith(button.strip().replace(" ", "")):
                        lista2 = line.find_all('button')
                        for line2 in lista2:
                            for line3 in line2.contents:
                                valores = line3.attrs.values()
                                for line4 in valores:
                                    for line5 in line4:
                                        if (type == 'add' and line5 == 'fa-plus') or (
                                                type == 'search' and line5 == 'fa-search') or (
                                                type == 'load' and line5 == 'fa-refresh'):
                                            cId = line2.attrs['id']
                                            element = self.driver.find_element_by_id(cId)
                                            break

            time.sleep(0.5)
            self.Click(element)
        except Exception as e:
            self.log_error(str(e))

    def SetGrid(self, btnFunc="Incluir"):
        '''
        Method to send values to a grid
        '''
        try:

            self.SetButton(btnFunc)
            self.tries = 1
            self.wait_elements_load(self.gridValues, "table")
            self.gridValues = []

        except Exception as e:
            self.log_error(str(e))

    def SelectBrowse(self, valores, opcao='', duplo=True):
        '''
		Method to select a option in a browse
		'''

        opt = ""
        lstValuesGrid = valores.split("|")
        lAchouTodos = False

        colunm = self.driver.find_elements_by_tag_name('tr')

        element = ""

        if opcao == '':
            for linha in colunm:
                for gridItem in lstValuesGrid:
                    if gridItem.replace(" ", "") in linha.text.replace(" ", "").replace("\n", ""):
                        lAchouTodos = True
                    else:
                        lAchouTodos = False
                        break

                if lAchouTodos:
                    element = linha

            if element == "":
                self.log_error('Não encontrou grid com conteúdo : ' + valores)

            if element:
                if duplo:
                    self.double_click(element)
                else:
                    self.Click(element)

        else:
            content = self.driver.page_source
            soup = BeautifulSoup(content, "html.parser")
            lista2 = soup.find_all("tr")

            for linha2 in lista2:
                for gridItem in lstValuesGrid:
                    if gridItem.replace(" ", "") in linha2.text.replace(" ", ""):
                        opt = self.driver.find_element_by_xpath("//*[@title='%s']" % opcao)
                        lAchouTodos = True
                    else:
                        lAchouTodos = False
                        break

                if lAchouTodos:
                    break

            if not lAchouTodos:
                self.log_error('Não encontrou grid com conteúdo : ' + lstValuesGrid)

            self.Click(opt)

    def Setup(self, lblUser="Usuário", lblPassword="Senha", btnAccess="Acessar Portal"):
        '''
        Fills the login screen
        '''
        self.SetValue(lblUser, self.config.user)
        self.SetValue(lblPassword, self.config.password)
        self.SetButton(btnAccess)

    def SwitchModal(self, option, frame=''):
        '''
        Sets the focus in a modal object
        '''
        try:
            time.sleep(2)
            self.driver.switch_to.default_content()
            self.driver.implicitly_wait(30)
            modaldupGuia = self.wait.until(EC.presence_of_element_located((By.ID, "modal-content")))

            if modaldupGuia.is_displayed():
                btn = self.driver.find_element_by_xpath("//button[contains(text(), '%s')]" % option)
                btn.click()
            else:
                time.sleep(2)
                if modaldupGuia.is_displayed():
                    btn = self.driver.find_element_by_xpath("//button[contains(text(), '%s')]" % option)
                    btn.click()
        except Exception as e:
            self.log_error(str(e))

    def SwitchWindow(self, exit=False):
        '''
        Sets the focus in the active window
        '''
        try:
            if exit == False:

                for handle in self.driver.window_handles:
                    self.driver.switch_to.window(handle)
            else:
                self.driver.close()
                for handle in self.driver.window_handles:
                    self.driver.switch_to.window(handle)
        except Exception as e:
            self.log_error(str(e))

    def SearchValue(self, busca, valor, grid=False, btnOk='ok', btnFind='buscar', searchparam='Pesquisar'):
        '''
        Searches for a register
        '''
        try:
            if grid == True:
                self.gridValues.extend([valor])

            self.driver.switch_to.default_content()
            self.driver.implicitly_wait(30)
            self.wait.until(EC.presence_of_element_located((By.ID, "modal-content")))

            self.tries = 1
            self.wait_elements_load("buscar", 'button')

            content = self.driver.page_source
            soup = BeautifulSoup(content, "html.parser")
            listselect = soup.find_all('select')
            listfield = soup.find_all('input')
            btnsearch = soup.find_all('button')
            for select in listselect:
                listselect2 = soup.find_all('option')
                for option in listselect2:
                    if option.text.strip() == busca.strip():
                        option2 = select.attrs['name']
                        element = self.driver.find_element_by_name(option2)
                        element.send_keys(busca)
                        break

            # searchparam = 'Pesquisar'
            for field in listfield:
                if 'placeholder' not in field.attrs:
                    continue
                else:
                    searchfield = field.attrs['placeholder']
                    if searchparam.strip() == searchfield.strip():
                        searchfieldID = field.attrs['id']
                        print(searchfieldID)
                        element = self.driver.find_element_by_id(searchfieldID)
                        element.send_keys(valor)
                        break

            # btnFind = 'buscar'
            for searchbtn in btnsearch:
                if btnFind.strip() == searchbtn.text.strip():
                    btnclick = searchbtn.attrs['name']
                    element = self.driver.find_element_by_name(btnclick)
                    element.click()
                    break

            time.sleep(1)
            # btnOk = 'ok'
            for searchbtn in btnsearch:
                if btnOk.strip() == searchbtn.text.strip():
                    btnclick = searchbtn.attrs['name']
                    element = self.driver.find_element_by_name(btnclick)
                    element.click()
                    break

            self.driver.switch_to.default_content()
        except Exception as e:
            self.log_error(str(e))

    def SetValue(self, campo, valor, grid=False, linha=0, chknewline=False, disabled=False):
        '''
        Includes values in a field
        '''
        try:
            if grid == True:
                self.gridValues.extend([valor])

            self.classe = "apw"
            self.elementDisabled = False
            self.tries = 1
            self.wait_elements_load(campo, 'label')
            self.input_value(campo, valor)
        except Exception as e:
            self.log_error(str(e))

    def WaitModal(self, text, opcao="title"):
        '''
        Waits for a modal object with a value on title
        '''
        self.driver.switch_to.default_content()
        self.tries = 1
        self.wait_elements_load(text, opcao)
        if self.IdRet == "":
            self.log_error('Não encontrada Modal com título: ' + text)
        else:
            modaldupGuia = self.wait.until(EC.presence_of_element_located((By.ID, "modal-content")))

    ######################### Métodos internos da classe ####################################
    #########################     Class Inner Methods    ####################################
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
                element = self.web_scrap(field, scrap_type=enum.ScrapType.TEXT, label=True)
            if not element:
                continue

            #preparing variables that would be used
            main_element = element

            #Aguardando campo ser carregado em tela
			#Waiting for field to be loaded in the screen

            element_first_children = next((x for x in element.contents if x.name in ["input", "select", "textarea"]), None)
            if element_first_children is not None:
                main_element = element_first_children

            else:
                element_div = next((x for x in element.contents if x.name in ["div"]), None)
                element_first_children = next((x for x in element_div.contents if x.name in ["input", "select", "textarea"]), None)
                main_element = element_first_children
            try:
                input_field = lambda: self.driver.find_element_by_xpath(xpath_soup(main_element))
            except:
                time.sleep(1)
                input_field = lambda: self.driver.find_element_by_xpath(xpath_soup(main_element))

            valtype = "C"

            main_value = value

            try:
                if not input_field().is_enabled() or "disabled" in main_element.attrs:
                    self.log_error(self.create_message(['', field],enum.MessageType.DISABLED))
            except:
                time.sleep(1)
                if not input_field().is_enabled() or "disabled" in main_element.attrs:
                    self.log_error(self.create_message(['', field],enum.MessageType.DISABLED))

            cId = main_element.attrs['id']

            self.tries = 1
            self.wait_elements_load(cId, main_element.name)


            time.sleep(0.5)

            if main_element.name == 'select':

                self.SetComboBox(cId, main_value)

                success = True

            else:
                try:
                    input_field().clear()
                    self.send_keys(input_field(), main_value)
                    self.send_keys(input_field(), Keys.TAB)

                    current_value = self.get_web_value(input_field()).strip()

                    if "fakepath" in current_value:
                        success = True
                    else:
                        success = current_value == main_value

                except:
                    continue

            if not success:
                self.log_error(f"Could not input value {value} in field {field}")

    def get_web_value(self, element):
        """
		Gets the informations of field based in the ID
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

    def Click(self, element):
        '''
		Execute a click in a button
		'''

        try:
            self.scroll_to_element(element)
            self.driver.execute_script("arguments[0].click();", element)

        except Exception:
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            self.scroll_to_element(element)
            actions.click()
            actions.perform()

    def wait_elements_load(self, noElement, type='', frames=''):
        '''
		Waits until a element to be present
		'''
        content = self.driver.page_source
        soup = BeautifulSoup(content, "html.parser")
        lAchouTodos = False

        if type == 'button':

            lista = soup.find_all(['button', 'input'])

            for a in lista:
                if ('value' in a.attrs and a.attrs['value'].strip() == noElement.strip()) or (
                a.text.strip().replace("\n", "").startswith(noElement.strip())):
                    self.tries = 0

                    if 'id' not in a.attrs:
                        self.IdRet = ''
                    else:
                        self.IdRet = a.attrs['id']

                    break
        elif type == 'label':
            self.IdRet = ''
            lista = soup.find_all('label')

            for a in lista:
                if a.text.strip().replace("\n", "").startswith(noElement.strip()):
                    self.tries = 0
                    break
        elif type == 'title':
            self.IdRet = ''
            a = soup.find('div', {"id": "modal-header"})

            if a is not None and a.text.strip().replace("\n", "").replace("×", "").startswith(noElement.strip()):
                self.tries = 0
                self.IdRet = noElement.strip()
        elif type == 'table':

            # Se for Table, o noElement vem carregado com uma lista de itens a serem pesquisados dentro da gride afim de verificar se o registro existe ou não.
            self.IdRet = ''
            lista2 = soup.find_all("tr")

            for linha2 in lista2:
                for gridItem in noElement:
                    if gridItem in linha2.text.replace(" ", "").replace("\n", ""):
                        lAchouTodos = True
                    else:
                        lAchouTodos = False
                        break

                if lAchouTodos:
                    break

            if lAchouTodos:
                self.tries = 0
                self.IdRet = "Grid Encontrada"

        elif type in ['input', 'select', 'textarea']:
            self.IdRet = ''
            lista = soup.find_all(type)

            for a in lista:
                if 'id' in a.attrs:
                    if noElement == a.attrs['id']:
                        try:
                            self.wait.until(EC.element_to_be_clickable((By.ID, noElement)))
                            self.tries = 0
                            break
                        except:
                            time.sleep(0.5)

        else:
            self.IdRet = ''
            lista = soup.find_all('a')

            for a in lista:
                if a.text.strip().replace("\n", "").startswith(noElement.strip()):
                    if 'id' in a.attrs:
                        self.wait.until(EC.element_to_be_clickable((By.ID, a.attrs['id'])))
                    self.tries = 0
                    break

        if self.tries != 0 and self.tries <= 20:

            self.driver.switch_to.default_content()

            content = self.driver.page_source
            soup = BeautifulSoup(content, "html.parser")
            lista = soup.find_all('iframe')

            for frame2 in lista:
                try:

                    if frames.find(frame2.attrs['id']) == -1:
                        frames = frames + ";" + frame2.attrs['id']
                        self.driver.switch_to.frame(frame2.attrs['id'])
                        self.wait_elements_load(noElement, type, frames)
                    else:
                        continue

                    if self.tries == 0:
                        frames = ''
                        break

                except Exception:
                    pass

        if self.tries != 0 and self.tries <= 20:
            self.tries += 1
            time.sleep(0.5)
            self.wait_elements_load(noElement, type)

    def SetComboBox(self, Id, cText):
        '''
		Selects a value in a combobox
		'''
        try:

            select = Select(self.driver.find_element_by_id('%s' % Id))

            # select by visible text
            select.select_by_visible_text(cText)

        except Exception as e:
            self.log_error(str(e))

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

    # Métodos importados da classe base
    # Imported methods from base class
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
        element = next(iter(list(map(lambda x: self.find_first_div_parent(x), container.find_all(text=re.compile(f"^{re.escape(label_text)}" + r"(\*?)(\s*?)$"))))), None)
        if element is None:
            return []

        return element

        '''
        next_sibling = element.find_next_sibling("input")
        # next_input = element.contents.find("input")
        if next_sibling:
        # if next_input:
            return [next_sibling]
            # return [next_input]
        else:
            return []
        '''

    def send_keys(self, element, arg):
        """
        [Internal]

        Clicks two times on the Selenium element.

        :param element: Selenium element
        :type element: Selenium object
        :param arg: Text or Keys to be sent to the element
        :type arg: string or selenium.webdriver.common.keys

        Usage:

        >>> #Defining the element:
        >>> element = lambda: self.driver.find_element_by_id("example_id")
        >>> #Calling the method with a string
        >>> self.send_keys(element(), "Text")
        >>> #Calling the method with a Key
        >>> self.send_keys(element(), Keys.ENTER)
        """
        try:
            element.send_keys("")
            element.send_keys(arg)
        except Exception:
            actions = ActionChains(self.driver)
            actions.move_to_element(element)
            actions.send_keys("")
            actions.send_keys(arg)
            actions.perform()

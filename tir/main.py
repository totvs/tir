from tir.technologies.webapp_internal import WebappInternal
from tir.technologies.apw_internal import ApwInternal

"""
This file must contain the definition of all User Classes.

These classes will contain only calls to the Internal classes.
"""

class Webapp():
    """
    Instantiates the Webapp automated interface testing class.
    """
    def __init__(self, config_path=""):
        self.__webapp = WebappInternal()

    def AddParameter(self, parameter, branch, portuguese_value="", english_value="", spanish_value=""):
        """
        Adds a parameter to the queue of parameters to be set by SetParameters method.

        :param parameter: The parameter name.
        :type parameter: str
        :param branch: The branch to be filled in parameter edit screen.
        :type branch: str
        :param portuguese_value: The value for a portuguese repository.
        :type portuguese_value: str
        :param english_value: The value for an english repository.
        :type english_value: str
        :param spanish_value: The value for a spanish repository.
        :type spanish_value: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.AddParameter("MV_MVCSA1", "", ".F.", ".F.", ".F.")
        """
        self.__webapp.AddParameter(parameter, branch, portuguese_value, english_value, spanish_value)

    def AssertFalse(self):
        """
        Defines that the test case expects a False response to pass

        Usage:

        >>> #Instantiating the class
        >>> inst.oHelper = Webapp()
        >>> #Calling the method
        >>> inst.oHelper.AssertFalse()
        """
        self.__webapp.AssertFalse()

    def AssertTrue(self):
        """
        Defines that the test case expects a True response to pass

        Usage:

        >>> #Instantiating the class
        >>> inst.oHelper = Webapp()
        >>> #Calling the method
        >>> inst.oHelper.AssertTrue()
        """
        self.__webapp.AssertTrue()

    def ChangeEnvironment(self):
        """
        Clicks on the change environment area of Protheus Webapp and
        fills the environment screen with the values passed on the Setup method.

        Usage:

        >>> # Calling the method:
        >>> oHelper.ChangeEnvironment()
        """
        self.__webapp.ChangeEnvironment()

    def CheckResult(self, field, user_value, grid=False, line=1, grid_number=1):
        """
        Checks if a field has the value the user expects.

        :param field: The field or label of a field that must be checked.
        :type field: str
        :param user_value: The value that the field is expected to contain.
        :type user_value: str
        :param grid: Boolean if this is a grid field or not. - **Default:** False
        :type grid: bool
        :param line: Grid line that contains the column field to be checked.- **Default:** 1
        :type line: int
        :param grid_number: Grid number of which grid should be checked when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling method to check a value of a field:
        >>> oHelper.CheckResult("A1_COD", "000001")
        >>> #-----------------------------------------
        >>> # Calling method to check a field that is on the second line of a grid:
        >>> oHelper.CheckResult("Client", "000001", grid=True, line=2)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Calling method to check a field that is on the second grid of the screen:
        >>> oHelper.CheckResult("Order", "000001", grid=True, line=1, grid_number=2)
        >>> oHelper.LoadGrid()
        """
        self.__webapp.CheckResult(field, user_value, grid, line, grid_number)

    def CheckView(self, text, element_type="help"):
        """
        Checks if a certain text is present in the screen at the time and takes an action.

        "help" - closes element.

        :param text: Text to be checked.
        :type text: str
        :param element_type: Type of element. - **Default:** "help"
        :type element_type: str

        Usage:

        >>> # Calling the method.
        >>> oHelper.CheckView("Processing")
        """
        self.__webapp.CheckView(text, element_type)

    def ClickBox(self, fields, contents_list="", select_all=False, browse_index=1):
        """
        Clicks on Checkbox elements of a grid.

        :param field: The column to identify grid rows.
        :type field: str
        :param content_list: Comma divided string with values that must be checked. - **Default:** "" (empty string)
        :type content_list: str
        :param select_all: Boolean if all options should be selected. - **Default:** False
        :type select_all: bool
        :param grid_number: Grid number of which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method to select a specific checkbox:
        >>> oHelper.ClickBox("Branch", "D MG 01 ")
        >>> #--------------------------------------------------
        >>> # Calling the method to select multiple checkboxes:
        >>> oHelper.ClickBox("Branch", "D MG 01 , D RJ 02")
        >>> #--------------------------------------------------
        >>> # Calling the method to select all checkboxes:
        >>> oHelper.ClickBox("Branch", select_all=True)
        """
        self.__webapp.ClickBox(fields, contents_list, select_all, browse_index)

    def ClickFolder(self, item):
        """
        Clicks on folder elements on the screen.

        :param folder_name: Which folder item should be clicked.
        :type folder_name: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickFolder("Folder1")
        """
        self.__webapp.ClickFolder(item)

    def ClickGridCell(self, column, row=1, grid_number=1):
        """
        Clicks on a Cell of a Grid.

        :param column: The column that should be clicked.
        :type column: str
        :param row_number: Grid line that contains the column field to be checked.- **Default:** 1
        :type row_number: int
        :param grid_number: Grid number of which grid should be checked when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.ClickGridCell("Product", 1)
        """
        self.__webapp.ClickGridCell(column, row, grid_number)

    def ClickIcon(self, icon_text):
        """
        Clicks on an Icon button based on its tooltip text.

        :param icon_text: The tooltip text.
        :type icon_text: str

        Usage:

        >>> # Call the method:
        >>> oHelper.ClickIcon("Add")
        >>> oHelper.ClickIcon("Edit")
        """
        self.__webapp.ClickIcon(icon_text)

    def GetValue(self, cabitem, field):
        """
        Gets the current value or text of element.

        :param field: The field or label of a field that must be checked.
        :type field: str
        :param grid: Boolean if this is a grid field or not. - **Default:** False
        :type grid: bool
        :param line: Grid line that contains the column field to be checked.- **Default:** 1
        :type line: int
        :param grid_number: Grid number of which grid should be checked when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method:
        >>> current_value = oHelper.GetValue("A1_COD")
        """
        return self.__webapp.GetValue(cabitem, field)

    def LoadGrid(self):
        """
        This method is responsible for running all actions of the input and check queues
        of a grid. After running, the queues would be empty.

        Must be called after SetValue and CheckResult calls that has the grid parameter set to True.

        Usage:

        >>> # After SetValue:
        >>> oHelper.SetValue("A1_COD", "000001", grid=True)
        >>> oHelper.LoadGrid()
        >>> #--------------------------------------
        >>> # After CheckResult:
        >>> oHelper.CheckResult("A1_COD", "000001", grid=True, line=1)
        >>> oHelper.LoadGrid()
        """
        self.__webapp.LoadGrid()

    def LogOff(self):
        """
        Logs out of the Protheus Webapp.

        Usage:

        >>> # Calling the method.
        >>> oHelper.LogOff()
        """
        self.__webapp.LogOff()

    def MessageBoxClick(self, button_text):
        """
        Clicks on desired button inside a Messagebox element.

        :param button_text: Desired button to click.
        :type button_text: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.MessageBoxClick("Ok")
        """
        self.__webapp.MessageBoxClick(button_text)

    def Program(self, program_name):
        """
        Method that sets the program in the initial menu search field.

        :param program_name: The program name
        :type program_name: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.Program("MATA020")
        """
        self.__webapp.Program(program_name)

    def RestoreParameters(self):
        """
        Restores parameters to previous value in CFG screen. Should be used after a **SetParameters** call.

        Usage:

        >>> # Adding Parameter:
        >>> oHelper.AddParameter("MV_MVCSA1", "", ".F.", ".F.", ".F.")
        >>> # Calling the method:
        >>> oHelper.SetParameters()
        """
        self.__webapp.RestoreParameters()

    def SearchBrowse(self, term, key_description=None, identifier=None):
        """
        Searchs a term on Protheus Webapp.

        It will search using the default search key, but if a **key** is provided
        it will search using the chosen key.

        It will search using the first search box on the screen, but if an **identifier**
        is provided, it will search on the chosen search box.

        :param term: The term that must be searched.
        :type term: str
        :param key: The search key to be chosen on the search dropdown. - **Default:** None
        :type key: str
        :param identifier: The identifier of the search box. If none is provided, it defaults to the first of the screen. - **Default:** None
        :type identifier: str

        Usage:

        >>> # To search using the first search box and default search key:
        >>> oHelper.SearchBrowse("D MG 001")
        >>> #------------------------------------------------------------------------
        >>> # To search using the first search box and a chosen key:
        >>> oHelper.SearchBrowse("D MG 001", key="Branch+id")
        >>> #------------------------------------------------------------------------
        >>> # To search using a chosen search box and the default search key:
        >>> oHelper.SearchBrowse("D MG 001", identifier="Products")
        >>> #------------------------------------------------------------------------
        >>> # To search using a chosen search box and a chosen search key:
        >>> oHelper.SearchBrowse("D MG 001", key="Branch+id", identifier="Products")
        """
        self.__webapp.SearchBrowse(term, key_description, identifier)

    def SetBranch(self, branch):
        """
        Chooses the branch on the branch selection screen.

        :param branch: The branch that would be chosen.
        :type branch: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetBranch("D MG 01 ")
        """
        self.__webapp.SetBranch(branch)

    def SetButton(self, button, sub_item=""):
        """
        Method that clicks on a button on the screen.

        :param button: Button to be clicked.
        :type button: str
        :param sub_item: Sub item to be clicked inside the first button. - **Default:** "" (empty string)
        :type sub_item: str

        Usage:

        >>> # Calling the method to click on a regular button:
        >>> oHelper.SetButton("Add")
        >>> #-------------------------------------------------
        >>> # Calling the method to click on a sub item inside a button.
        >>> oHelper.SetButton("Other Actions", "Process")
        """
        self.__webapp.SetButton(button, sub_item)

    def SetFilePath(self, value):
        """
        Fills the path screen with desired path.

        :param value: Path to be inputted.
        :type value: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetFilePath(r"C:\\folder")
        """
        self.__webapp.SetFilePath(value)

    def SetFocus(self, field):
        """
        Sets the current focus on the desired field.

        :param field: The field that must receive the focus.
        :type field: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetFocus("A1_COD")
        """
        self.__webapp.SetFocus(field)

    def SetKey(self, key, grid=False, grid_number=1):
        """
        Press the desired key on the keyboard on the focused element.

        Supported keys: F1 to F12, Up, Down, Left, Right, Enter and Delete

        :param key: Key that would be pressed
        :type key: str
        :param grid: Boolean if action must be applied on a grid. (Usually with DOWN key)
        :type grid: bool
        :param grid_number: Grid number of which grid should be used when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetKey("ENTER")
        >>> #--------------------------------------
        >>> # Calling the method on a grid:
        >>> oHelper.SetKey("DOWN", grid=True)
        >>> #--------------------------------------
        >>> # Calling the method on the second grid on the screen:
        >>> oHelper.SetKey("DOWN", grid=True, grid_number=2)
        """
        self.__webapp.SetKey(key, grid, grid_number)

    def SetLateralMenu(self, menuitens):
        """
        Navigates through the lateral menu using provided menu path.
        e.g. "MenuItem1 > MenuItem2 > MenuItem3"

        :param menu_itens: String with the path to the menu.
        :type menu_itens: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetLateralMenu("Updates > Registers > Products > Groups")
        """
        self.__webapp.SetLateralMenu(menuitens)

    def SetParameters(self):
        """
        Sets the parameters in CFG screen. The parameters must be passed with calls for **AddParameter** method.

        Usage:

        >>> # Adding Parameter:
        >>> oHelper.AddParameter("MV_MVCSA1", "", ".F.", ".F.", ".F.")
        >>> # Calling the method:
        >>> oHelper.SetParameters()
        """
        self.__webapp.SetParameters()

    def SetTabEDAPP(self, table_name):
        """
        Chooses the table on the generic query (EDAPP).

        :param table: The table that would be chosen.
        :type table: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.SetTabEDAPP("AAB")
        """
        self.__webapp.SetTabEDAPP(table_name)

    def SetValue(self, field, value, grid=False, grid_number=1, ignore_case=True):
        """
        Sets value of an input element.

        :param field: The field name or label to receive the value
        :type field: str
        :param value: The value to be inputted on the element.
        :type value: str
        :param grid: Boolean if this is a grid field or not. - **Default:** False
        :type grid: bool
        :param grid_number: Grid number of which grid should be inputted when there are multiple grids on the same screen. - **Default:** 1
        :type grid_number: int
        :param ignore_case: Boolean if case should be ignored or not. - **Default:** True
        :type ignore_case: bool

        Usage:

        >>> # Calling method to input value on a field:
        >>> oHelper.SetValue("A1_COD", "000001")
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field that is a grid:
        >>> oHelper.SetValue("Client", "000001", grid=True)
        >>> oHelper.LoadGrid()
        >>> #-----------------------------------------
        >>> # Calling method to input value on a field that is on the second grid of the screen:
        >>> oHelper.SetValue("Order", "000001", grid=True, grid_number=2)
        >>> oHelper.LoadGrid()
        """
        self.__webapp.SetValue(field, value, grid, grid_number, ignore_case)

    def Setup(self, initial_program,  date="", group="99", branch="01", module=""):
        """
        Prepare the Protheus Webapp for the test case, filling the needed information to access the environment.

        :param initial_program: The initial program to load.
        :type initial_program: str
        :param date: The date to fill on the environment screen. - **Default:** "" (empty string)
        :type date: str
        :param group: The group to fill on the environment screen. - **Default:** "99"
        :type group: str
        :param branch: The branch to fill on the environment screen. - **Default:** "01"
        :type branch: str
        :param module: The module to fill on the environment screen. - **Default:** "" (empty string)
        :type module: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.Setup("SIGAFAT", "18/08/2018", "T1", "D MG 01 ")
        """
        self.__webapp.Setup(initial_program, date, group, branch, module)

    def TearDown(self):
        """
        Closes the webdriver and ends the test case.

        Usage:

        >>> #Instantiating the class
        >>> inst.oHelper = Webapp()
        >>> #Calling the method
        >>> inst.oHelper.TearDown()
        """
        self.__webapp.TearDown()

    def WaitShow(self, itens):
        """
        Search string that was sent and wait show the elements.
        e.g. "Item1,Item2,Item3"

        :param itens: List of itens that will hold the wait.
        :type itens: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitShow("Processing")
        """
        self.__webapp.WaitShow(itens)

    def WaitHide(self, itens):
        """
        Search string that was sent and wait hide the elements.
        e.g. "Item1,Item2,Item3"

        :param itens: List of itens that will hold the wait.
        :type itens: str

        Usage:

        >>> # Calling the method:
        >>> oHelper.WaitHide("Processing")
        """
        self.__webapp.WaitHide(itens)

class Apw():

    def __init__(self, config_path=""):

        self.__Apw = ApwInternal()

    def CheckBrowse(self, valores):

        self.__Apw.CheckBrowse(valores)


    def CheckLink(self, Link):

        self.__Apw.CheckLink(Link)


    def ClickLink(self, Link):

        self.__Apw.ClickLink(Link)

    def ClickMenu(self, caminho):

        self.__Apw.ClickMenu(caminho)


    def CloseAlert(self):

        self.__Apw.CloseAlert()

    def CloseWindow(self):

        self.__Apw.CloseWindow()

    def EndCase(self):

        self.__Apw.EndCase()

    def SetButton(self, button, type=''):

        self.__Apw.SetButton(button, type)

    def SetGrid(self, btnFunc="Incluir"):

        self.__Apw.SetGrid(btnFunc)

    def SelectBrowse(self, valores, opcao='', duplo=True):

        self.__Apw.SelectBrowse(valores, opcao, duplo)

    def Setup(self, lblUser="Usuário", lblPassword="Senha", btnAccess="Acessar Portal"):

        self.__Apw.Setup(lblUser, lblPassword, btnAccess)

    def SwitchModal(self, opcao, frame=''):

        self.__Apw.SwitchModal(opcao, frame)

    def SwitchWindow(self, exit=False):

        self.__Apw.SwitchWindow(exit)

    def SearchValue(self, busca, valor, grid=False, btnOk='ok', btnFind='buscar', searchparam='Pesquisar'):

        self.__Apw.SearchValue(busca, valor, grid, btnOk, btnFind, searchparam)

    def SetValue(self, campo, valor, grid=False, linha=0, chknewline=False, disabled=False):

        self.__Apw.SetValue(campo, valor, grid, linha, chknewline, disabled)

    def WaitModal(self, text, opcao="title"):

        self.__Apw.WaitModal(text, opcao)

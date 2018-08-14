from tir.technologies.webapp_internal import WebappInternal

class Webapp():
    '''
    Instantiates the Webapp automated interface testing class.
    '''
    def __init__(self, config_path=""):
        self.__webapp = WebappInternal()

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
        Clicks on the Change Environment button and sets the new environment.

        Usage:

        >>> #Calling the method:
        >>> inst.oHelper.ChangeEnvironment()
        """
        self.__webapp.ChangeEnvironment()

    def CheckResult(self, field, user_value, grid=False, line=1, grid_number=1):
        '''
        Validates if a field on the interface has the expected value
        '''
        self.__webapp.CheckResult(field, user_value, grid, line, grid_number)

    def CheckView(self, text, element_type="help"):
        '''
        Checks if a certain text is present in the screen at the time.
        '''
        self.__webapp.CheckView(text, element_type)

    def ClickBox(self, fields, contents_list="", select_all=False, browse_index=1):
        '''
        Method that clicks in checkbox
        '''
        self.__webapp.ClickBox(fields, contents_list, select_all, browse_index)

    def ClickFolder(self, item):
        '''
        Clicks on a folder
        '''
        self.__webapp.ClickFolder(item)

    def GetValue(self, cabitem, field):
        '''
        Returns a web value from DOM elements.
        '''
        return self.__webapp.GetValue(cabitem, field)

    def LoadGrid(self):
        '''
        Load the grid fields
        '''
        self.__webapp.LoadGrid()

    def LogOff(self):
        '''
        Log off the system.
        '''
        self.__webapp.LogOff()

    def Program(self, program_name):
        '''
        Sets the program name in the search box.
        '''
        self.__webapp.Program(program_name)

    def RestoreParameters(self):
        '''
        Restores parameters altered by the method SetParameters.
        '''
        self.__webapp.RestoreParameters()

    def SearchBrowse(self, term, key_description, identifier=None):
        '''
        Searches the term based on the key_description and identifier.
        '''
        self.__webapp.SearchBrowse(term, key_description, identifier)

    def SetBranch(self, branch):
        '''
        Sets the branch to be used.
        '''
        self.__webapp.SetBranch(branch)

    def SetButton(self, button, sub_item=""):
        '''
        Clicks on a button on the interface.
        '''
        self.__webapp.SetButton(button, sub_item)

    def SetFocus(self, field):
        '''
        Sets the current focus on the desired field.
        '''
        self.__webapp.SetFocus(field)

    def SetKey(self, key, grid=False, grid_number=1):
        '''
        Press the desired key on the keyboard on the focused element.

        Supported keys: F1 to F12, Up, Down, Left, Right, Enter and Delete
        '''
        self.__webapp.SetKey(key, grid, grid_number)

    def SetLateralMenu(self, menuitens):
        '''
        Navigates through the lateral menu using provided menu path.

        e.g. “MenuItem1 > MenuItem2 > MenuItem3”
        '''
        self.__webapp.SetLateralMenu(menuitens)

    def SetParameters(self, array_parameters):
        '''
        Sets the parameters on Protheus' config.
        '''
        self.__webapp.SetParameters(array_parameters)

    def SetTabEDAPP(self, table_name):
        '''
        Sets the table name on the search field of EDAPP routine.
        '''
        self.__webapp.SetTabEDAPP(table_name)

    def SetValue(self, field, value, grid=False, grid_number=1, disabled=False, ignore_case=True):
        '''
        Sets the value on the desired field.
        '''
        self.__webapp.SetValue(field, value, grid, grid_number, disabled, ignore_case)

    def Setup(self, initial_program,  date="", group="99", branch="01", module=""):
        '''
        Fills the initial screens of Protheus.

        Initial Program, User and Environment.
        '''
        self.__webapp.Setup(initial_program, date, group, branch, module)

    def TearDown(self):
        '''
        Closes the webdriver and ends the test case.

        Usage:

        >>> #Instantiating the class
        >>> inst.oHelper = Webapp()
        >>> #Calling the method
        >>> inst.oHelper.TearDown()
        '''
        self.__webapp.TearDown()

    def WaitUntil(self, itens):
        '''
        Search string that was sent and wait until condition is true

        e.g. “Item1,Item2,Item3”
        '''
        self.__webapp.WaitUntil(itens)

    def WaitWhile(self, itens):
        '''
        Search string that was sent and wait while condition is true

        e.g. “Item1,Item2,Item3”
        '''
        self.__webapp.WaitWhile(itens)

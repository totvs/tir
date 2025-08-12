Config.json
============

The environment must be configured through a `config.json <https://github.com/totvs/tir/blob/main/config.json>`__ file.

You can find one to be used as a base in this repository. To select your file,
you can either put it in your workspace or pass its path as a parameter of any of our classes' initialization.
The config.json file is where the configs of the tests are defined.

These are the accepted config keys, and whether they are required or not:

Structure (exemple):
--------------------------

.. code-block:: json

   {
     "Url": "http://localhost:8080/",
     "Browser": "Firefox",
     "Environment": "MyProtheusEnvironment",
     "User": "MyUser",
     "Password": "MyP4ssW0rd123"
     "...", "..."
   }



Execution Parameters
---------------------


Required Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. list-table:: Required Parameters
   :header-rows: 1
   :widths: 15 10 50 25

   * - **Parameter**
     - **Type**
     - **Description**
     - **Example**
   * - **Url**
     - str
     - The URL that will run the tests.
     - http://localhost:8080/
   * - **Browser**
     - str
     - Browser used for execution. Firefox or Chrome.
     - Firefox
   * - **Environment**
     - str
     - Target Protheus environment.
     - MyProtheusEnvironment
   * - **User**
     - str
     - Username to login into the environment. 
     - MyUser
   * - **Password**
     - str
     - User password to login.
     - MyP4ssW0rd123
   * - **Language**
     - str
     - Language used in your protheus environment. Options: pt-br, en-us, es-es.
     - pt-br

********************************

POUI Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: POUI & UI Settings
   :header-rows: 1
   :widths: 15 10 50 25

   * - **Parameter**
     - **Type**
     - **Description**
     - **Example**
   * - POUI
     - bool
     - Enable POUI interface. Enable only if running POUI Tests outside Protheus environments. **Default:** false
     - false
   * - POUILogin
     - bool
     - Needed when APPENVIRONMENT key enabled in your environment using POUI login interface. *This paramter is deprecated and will be removed in >= 12.1.2510 version*
     - true
   * - SSOLogin
     - bool
     - Enable when login by SSO has been configured in the environment. Skips login screen.
     - true


********************************

Additional Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: General Settings
   :header-rows: 1
   :widths: 15 10 50 25

   * - **Parameter**
     - **Type**
     - **Description**
     - **Example**
   * - Headless
     - bool
     - Headless mode, meaning that the browser window wouldn’t be visible. **Default:** false
     - true
   * - DebugLog
     - bool
     - Show debug logs during execution. **Default:** false
     - true
   * - ScreenshotFolder
     - str
     - Path to send all screenshots taken during execution Screenshot method. **Default:** Current execution path
     - C:\\Path\\to\\folder
   * - ScreenShot
     - bool
     - Save screenshots in execution path in case of errors. **Default:** true
     - true
   * - TimeOut
     - int
     - Time set (in seconds) to expire the test if it is reached. **Default:** 90
     - 60
   * - SkipEnvironment
     - bool
     - Skips module selection screen. **Default:** false
     - true
   * - StartProgram
     - str
     - Start test case directly in url of seted program .
     - SIGAFAT
   * - Country
     - str
     - Country will be seted as main in log of execution.
     - BRA


********************************

Logging & Monitoring
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: Log Configuration
   :header-rows: 1
   :widths: 15 10 50 25

   * - **Parameter**
     - **Type**
     - **Description**
     - **Example**
   * - NewLog
     - bool
     - Enable new log by JSON API. **Default:** false
     - true
   * - MotExec
     - str
     - Identifier log tag
     - HOMOLOG_TIR
   * - ExecId
     - str
     - Execution ID for log tracking
     - 20201119
   * - LogUrl1
     - str
     - URL/API to send execution logs
     - http://127.0.0.1:3333/log/
   * - LogUrl2
     - str
     - Additional log server URL
     - http://10.171.78.43:8204/rest/LOGEXEC/
   * - LogFolder
     - str
     - Folder to save log files. **Default:** Script execution path
     - C:\\TIR\\Log
   * - LogFile
     - bool
     - Save log file. *Currently disabled*
     - 
   * - LogHttp
     - str
     - HTTP server to send Log folder by URL/HTTP
     - http://www.logtest.com.br/api/
   * - BaseLine_Spool
     - str
     - Path to report spool in your environment
     - acda080rbase.##r

********************************

Database Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This section contains optional parameters used to configure the database connection for your tests.
By specifying these settings in the config file, you avoid the need to 
provide connection details directly as parameters in the QueryExecute method.
This approach simplifies test setup and centralizes database configuration management.

.. list-table:: Database Settings
   :header-rows: 1
   :widths: 15 10 50 25

   * - **Parameter**
     - **Type**
     - **Description**
     - **Example**
   * - DBDriver
     - str
     - ODBC driver name or Oracle Driver name.
     - Oracle
   * - DBServer
     - str
     - Host address of the database
     - 10.171.83.18
   * - DBPort
     - str
     - Port number of the database. **Default:** 1521
     - 1521
   * - DBName
     - str
     - Database name
     - MyDatabase
   * - DBUser
     - str
     - Database user
     - MyUser
   * - DBPassword
     - str
     - Database password
     - MyDataB4s3P4ssW0rd123

********************************

Aditional Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: Advanced Settings
   :header-rows: 1
   :widths: 15 10 50 25

   * - **Parameter**
     - **Type**
     - **Description**
     - **Example**
   * - ParameterMenu
     - str
     - Custom path for parameter menu. Only for costumized environments*.
     - Updates > Parameters
   * - UserCfg
     - bool
     - Autofill user from config.json
     - true
   * - PasswordCfg
     - bool
     - Autofill password from config.json
     - true
   * - CSVPath
     - str
     - Path to CSV file used by OpenCSV to locate and read CSV files.
     - C:\\path\\to\\csv\\file
   * - ParameterUrl
     - Bool
     - Input Parameters in URL. If true, the parameters will be passed in the URL(Needs RPO package installed in Protheus Environment).
     - 
   * - Data Delimiter
     - str
     - Defines date delimiter format. Only for costumized date delimiters in protheus Environment.Example "22.02.20xx" instead "22/02/20xx"(dot or slash)
     - .


********************************

Chrome Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Only for Chrome browser.

.. list-table:: Chrome Settings
   :header-rows: 1
   :widths: 15 10 50 25

   * - **Parameter**
     - **Type**
     - **Description**
     - **Example**
   * - ChromeDriverAutoInstall
     - bool
     - Automatically install ChromeDriver. **Default:** false
     - true
   * - SSLChromeInstallDisable
     - bool
     - Disable SSL to allow driver download. **Default:** false
     - true

********************************

Versioning Info
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*This configuration can be used to skip the About menu.*

.. list-table:: Release & Version Info
   :header-rows: 1
   :widths: 15 10 50 25

   * - **Parameter**
     - **Type**
     - **Description**
     - **Example**
   * - LogInfoConfig
     - bool
     - Skip About menu (Needs to set Release, TopDataBase, Lib and Build)
     - true
   * - Release
     - str
     - Manual release version
     - 12.1.2410
   * - TopDataBase
     - str
     - Database version manually set
     - 
   * - Lib
     - str
     - Library version manually set
     - 
   * - Build
     - str
     - Build version manually set
     - 


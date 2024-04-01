Config.json
============

The config.json file is where the configs of the tests are defined.

These are the accepted config keys, and whether they are required or not:

- **Url:** The URL that will run the tests. **Required**
- **Browser:** Browser that will be used to run the tests. (Firefox or Chrome) **Required**
- **Environment:** Environment used to run the tests. **Required**
- **User:** User that will be logged into the environment. **Required**
- **Password:** Password to log  on to the environment. **Required**
- **Language:** Language to be considered in execution.
- **DebugLog:** Defines whether the run log will be displayed during tests.
- **TimeOut:** Time set to expire the test if it is reached.
- **SkipEnvironment** Skips the module selection screen, if your Protheus configuration does not have it.
- **Headless:** Defines whether the test will run with or without interface.
- **ScreenshotFolder**: A folder to contain all screenshots taken by the user with the Screenshot method.
- **NewLog**: (boolean) true to activate the new log.
- **MotExec**: Execution tag. Example: "MotExec":"HOMOLOG_TIR"
- **ExecId**: Execution id. Example: "ExecId":"20201119"
- **LogUrl1**: service url. Example: "LogUrl1":"http://127.0.0.1:3333/log/"
- **CheckValue**: Indicates if TIR must check each value after fill. Example: "CheckValue": true
- **POUILogin**: For new POUI login interface. Example: "POUILogin": true
- **ChromeDriverAutoInstall**: For chromedriver auto install. Example: "ChromeDriverAutoInstall": true
- **SSLChromeInstallDisable**: In some cases will be necessary deactivate ssl to download chromedriver automatically. Example: "SSLChromeInstallDisable": true
- **ScreenShot:** If applicable, add screenshots to help explain your problem.
- **Country:** Defines which country will be set as main. Example: pt-br
- **NumExec:** Returns Status, URL and ID for execution.
- **MotExec:** Checks the main content of MotExec key.
- **LogFolder:** Used for determinate the local you want save the log. Example "LogFolder": "C:\\TIR\\Log
- **LogFile:** Create a log csv file.
- **ParameterMenu:** Internal method of SetParameters and RestoreParameters.
- **UserCfg:** Fills the user login screen of Protheus with the user and password located on config.json
- **PasswordCfg:** Fills the user login screen of Protheus with the user and password located on config.json
- **BinPath:** Fix firefox options and chromeoptions. Remove obsolete drivers.
- **CSVPath:** This method return data as a string if necessary use some method to convert data like int(). Example: CSVPath : "C:\\temp"
- **DBDriver:** ODBC Driver database name
- **DBServer:** Database Server Name
- **DBPort:** Database port default port=1521
- **DBName:** Database Name
- **DBUser:** User Database Name
- **DBPassword:** Database password
- **DBQOracleServer:** Only for Oracle: DBQ format:Host:Port/oracle instance
- **URL_TSS:** Used for TSS only.
- **StartProgram:** Opens the browser maximized and goes to defined URL
- **LogUrl2:** Add default server address and save response log.
- **ParameterUrl:** Filter the correct value to fill
- **LogHttp:** Add folder to save log by loghttp structure
- **BaseLine_Spool:** Baseline_Spool is the path of report spool in your environment
- **POUI:** For new POUI login interface
- **LogInfoConfig:** Add set_log_info alternative
- **Release:** Get the current Release.
- **TopDataBase:** Get the current Data Base.
- **Lib:** Get the current Lib.
- **Build:** Get the current Lib.
- **Data Delimiter:** Used when you have a dot in the date instead of a slash.


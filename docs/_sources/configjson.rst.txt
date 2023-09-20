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

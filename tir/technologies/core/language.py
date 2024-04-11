class LanguagePack:
    '''
    This class is instantiated to contain the translation of terms of each supported language.
    '''
    def __init__(self, language="pt-BR"):

        languagepack = self.get_language_pack(language)

        self.user = languagepack["User"]
        self.password = languagepack["Password"]
        self.database = languagepack["Database"]
        self.group = languagepack["Group"]
        self.branch = languagepack["Branch"]
        self.environment = languagepack["Environment"]
        self.add = languagepack["Add"]
        self.delete= languagepack["Delete"]
        self.no_actions = {languagepack["Confirm"],languagepack["Save"],languagepack["Cancel"],languagepack["Close"],languagepack["Finish"]}
        self.edit = languagepack["Edit"]
        self.editar = languagepack["Editar"]
        self.cancel = languagepack["Cancel"]
        self.view = languagepack["View"]
        self.visualizar = languagepack["Visualizar"]
        self.other_actions = languagepack["Other Actions"]
        self.confirm = languagepack["Confirm"]
        self.save = languagepack["Save"]
        self.close = languagepack["Close"]
        self.exit = languagepack["Exit"]
        self.leave_page = languagepack["Leave Page"]
        self.enter = languagepack["Enter"]
        self.finish = languagepack["Finish"]
        self.details = languagepack["Details"]
        self.search = languagepack["Search"]
        self.Ok = languagepack["Ok"]
        self.copy = languagepack["Copy"]
        self.cut = languagepack["Cut"]
        self.paste = languagepack["Paste"]
        self.calculator = languagepack["Calculator"]
        self.spool = languagepack['Spool']
        self.help = languagepack['Help']
        self.folders = languagepack['Folders']
        self.generate_differential_file = languagepack['Generate Differential File']
        self.include = languagepack['Include']
        self.filter = languagepack['Filter']
        self.menu_about = languagepack["Menu About"]
        self.branches =  languagepack["Branches"]
        self.help = languagepack["Help"]
        self.problem = languagepack["Problem"]
        self.solution = languagepack["Solution"]
        self.change_environment = languagepack["Change Environment"]
        self.invert_selection = languagepack["Invert Selection"]
        self.parameter_menu = languagepack["Parameter Menu"]
        self.search2 = languagepack["Search 2"]
        self.search_by = languagepack["Search By"]
        self.From = languagepack["From"]
        self.To = languagepack["To"]
        self.coins = languagepack["Coins"]
        self.next = languagepack["Next"]
        self.logOff = languagepack["LogOff"]
        self.checkhelp = languagepack["Checkhelp"]
        self.checkproblem = languagepack["Checkproblem"]
        self.checksolution = languagepack["Checksolution"]
        self.change_password = languagepack["ChangePassword"]
        self.user_login = languagepack["UserLogin"]
        self.current_password = languagepack["CurrentPassword"]
        self.nem_password = languagepack["NewPassword"]
        self.confirm_new_password = languagepack["ConfirmNewPassword"]
        self.yes = languagepack["Yes"]
        self.assert_false_message = languagepack["AssertFalseMessage"]
        self.file_name = languagepack["File Name"]
        self.open = languagepack["Open"]
        self.warning = languagepack["Warning"]
        self.news = languagepack["News"]
        self.continue_string = languagepack["Continue"]
        self.shortconfirm = languagepack["Short Confirm"]
        self.confirm_in_environment_screen = languagepack["Enter in environment screen"]
        self.codecoverage = languagepack["Code Coverage"] #"Aguarde... Coletando informacoes de cobertura de codigo."
        self.release = languagepack["Release"]
        self.topdatabase = languagepack["Top DataBase"]
        self.libversion = languagepack["Lib Version"]
        self.build = languagepack["Build"]
        self.issued = languagepack["Issued"]
        self.ref_dt = languagepack["Ref.Dt"]
        self.time = languagepack["Time"]
        self.end_time = languagepack["End Time"]
        self.procedure_menu = languagepack["Procedure Menu"]
        self.code = languagepack["Code"]
        self.success = languagepack["Success"]
        self.procedure_install = languagepack["Procedure Install"]
        self.procedure_uninstall = languagepack["Procedure Uninstall"]
        
        self.messages = Messages(languagepack)

    def get_language_pack(self, language):

        english = {
            "User": "User",
            "Password": "Password",
            "Database": "Basedata",
            "Group": "Group",
            "Branch": "Branch",
            "Environment": "Environment",
            "Add": "Add",
            "Delete": "Delete",
            "Edit": "Edit",
            "Editar": "Edit", #usado num elemento especifico por conta do ambiente russo
            "Cancel": "Cancel",
            "View": "View",
            "Visualizar": "View", #usado num elemento especifico por conta do ambiente russo
            "Other Actions": "Other Actions",
            "Confirm": "Confirm",
            "Save": "Save",
            "Close": "Close",
            "Exit": "Exit",
            "Leave Page": "Exit page",
            "Enter": "Enter",
            "Finish": "Finish",
            "Details": "Details",
            "Search": "Search",
            "Ok": "Ok",
            "Copy": "Copy",
            "Cut": "Cut",
            "Paste": "Paste",
            "Calculator": "Calculator",
            "Spool": "Spool",
            "Folders": 'Folders',
            "Generate Differential File": "Generate Differential File",
            "Include": "Insert",
            "Filter": "Filter",
			"Menu About": "Help > About",
            "Error Log": "SMARTCLIENT a problem has been found while running it and this one will be concluded. For further information click on details.",
            "Error Log Print": "Error Log Print",
            "Error Msg Required": "This action could not be completed. There are mandatory fields not field.",
            "Help": "Help:",
            "Problem": "Problem:",
            "Solution": "Solution:",
            "Branches": "Branches",
            "Grid Steps Misuse": "Grid steps misuse. Be sure to only use a group of inputs or a group of checks in each Grid Block.",
            "Grid Steps Empty": "No grid steps were found. Be sure to only use a group of inputs or a group of checks in each Grid Block.",
            "Grid Line Error": "Line does not exist in current grid.",
            "Grid Column Error": "Column does not exist in current grid.",
            "Grid Number Error": "There is not that many grids on the current screen.",
            "Text Not Found": "Text Not Found.",
            "Help Not Found": "Help Not Found",
            "User Not Authenticated": "User Not Authenticated",
            "Change Environment": "Change environment",
            "Invert Selection": "Invert Selection",
            "Parameter Menu": "Environment > Registers > Parameters",
            "Search 2": "Search",
            "Search By": "Search by:",
            "From": "From",
            "To": "To",
            "Coins": "Coins",
            "Next": "Next >>",
            "LogOff": "Log Off",
            "Checkhelp": "Help:",
            "Checkproblem": "Problem:",
            "Checksolution": "Solution:",
            "ChangePassword": "Reserved",
            "UserLogin": "Reserved",
            "CurrentPassword": "Reserved",
            "NewPassword": "Reserved",
            "ConfirmNewPassword": "Reserved",
            "Yes": "Sim",
            "AssertFalseMessage": "AssertFalse method used without a checkpoint, check the script.",
            "File Name": "File Name",
            "Open": "Open",
            "Warning": "Warning",
            "News": "News",
            "Continue": "Continue",
            "Short Confirm": "Confirm",
            "Enter in environment screen": "Enter",
            "Code Coverage": "Aguarde... Coletando informacoes de cobertura de codigo.",
            "Release": "Release",
            "Top DataBase": "Top DataBase",
            "Lib Version": "Lib Version",
            "Build": "Build",
            "Issued": "Issued",
            "Ref.Dt": "Ref.Dt",
            "Time": "Time",
            "End Time": "End Time",
            "Procedure Menu": "Database > Dictionary > Stored Procedure",
            "Code": "Code",
            "Success": "Success",
            "Procedure Install": "Install selected processes",
            "Procedure Uninstall": "Remove selected processes"
            
        }

        brazilian_portuguese = {
            "User": "Usuário",
            "Password": "Senha",
            "Database": "Data base",
            "Group": "Grupo",
            "Branch": "Filial",
            "Environment": "Ambiente",
            "Add": "Incluir",
            "Delete": "Excluir",
            "Edit": "Editar",
            "Editar": "Editar", #usado num elemento especifico por conta do ambiente russo
            "Cancel": "Cancelar",
            "View": "Visualizar",
            "Visualizar": "Visualizar", #usado num elemento especifico por conta do ambiente russo
            "Other Actions": "Outras Ações",
            "Confirm": "Confirmar",
            "Save": "Salvar",
            "Close": "Fechar",
            "Exit": "Sair",
            "Leave Page": "Sair da página",
            "Enter": "Entrar",
            "Finish": "Finalizar",
            "Details": "Detalhes",
            "Search": "Pesquisar",
            "Ok": "Ok",
            "Copy": "Copiar",
            "Cut": "Recortar",
            "Paste": "Colar",
            "Calculator": "Calculadora",
            "Spool": "Spool",
            "Folders": 'Pastas',
            "Generate Differential File": "Gerar Arquivo Diferencial",
            "Include": "Incluir",
            "Filter": "Filtrar",
			"Menu About": "Ajuda > Sobre",
            "Error Log": "SMARTCLIENT encontrou um problema durante a execucao e sera finalizado. Para informacoes adicionais clique em detalhes",
            "Error Log Print": "SMARTCLIENT encontrou um problema durante a execucao e sera finalizado. Para informacoes adicionais verifique print efetuado da tela",
            "Error Msg Required": "Não é possível completar a ação. Existem campos obrigatórios não preenchidos.",
            "Help": "Ajuda:",
            "Problem": "Problema:",
            "Solution": "Solução:",
            "Branches": "Filiais",
            "Grid Steps Misuse": "Uso de grid errado. Passe apenas um grupo de inputs ou um grupo de checks em cada bloco de grid.",
            "Grid Steps Empty": "Nenhum passo de grid encontrado. Passe um grupo de inputs ou um grupo de checks em cada bloco de grid.",
            "Grid Line Error": "Linha não existe na grid atual.",
            "Grid Column Error": "Coluna não existe na grid atual.",
            "Grid Number Error": "Não existe essa quantidade de grids na tela atual.",
            "Text Not Found": "Texto não encontrado.",
            "Help Not Found": "Help não encontrado.",
            "User Not Authenticated": "Usuário não autenticado",
            "Change Environment": "Trocar módulo",
            "Invert Selection": "Inverte Seleção",
            "Parameter Menu": "Ambiente > Cadastros > Parâmetros",
            "Search 2": "Buscar",
            "Search By": "Procurar por:",
            "From": "De",
            "To": "Ate",
            "Coins": "Moedas",
            "Next": "Avançar >>",
            "LogOff": "Log Off",
            "Checkhelp": "Help:",
            "Checkproblem": "Problema:",
            "Checksolution": "Solução:",
            "ChangePassword": "Alterar Senha",
            "UserLogin": "Login do usuário",
            "CurrentPassword": "Senha atual",
            "NewPassword": "Nova senha",
            "ConfirmNewPassword": "Confirmar nova senha",
            "Yes": "Sim",
            "AssertFalseMessage": "Método AssertFalse utilizado sem um ponto de verificação, verifique o script.",
            "File Name": "Nome do Arquivo",
			"Open": "Abrir",
            "Warning": "Atenção",
            "News": "Novidades do",
            "Continue": "Continuar",
            "Short Confirm": "Confirmar",
            "Enter in environment screen": "Entrar",
            "Code Coverage": "Aguarde... Coletando informacoes de cobertura de codigo.",
            "Release": "Release",
            "Top DataBase": "Top DataBase",
            "Lib Version": "Versão da lib",
            "Build": "Build",
            "Issued": "Emissão",
            "Ref.Dt": "DT.Ref.",
            "Time": "Hora",
            "End Time": "Hora Término",
            "Procedure Menu": "Base de Dados > Dicionário > Stored Procedure",
            "Code": "Código",
            "Success": "Sucessos",
            "Procedure Install": "Instalar processos selecionados",
            "Procedure Uninstall": "Remover processos selecionados"
        }
        spanish = {
            "User": "Usuário",
            "Password": "Senha",
            "Database": "Fecha base",
            "Group": "Grupo",
            "Branch": "Sucursal",
            "Environment": "Entorno",
            "Add": "Incluir",
            "Delete": "Excluir",
            "Edit": "Editar",
            "Editar": "Editar", #usado num elemento especifico por conta do ambiente russo
            "Cancel": "Anular",
            "View": "Visualizar",
            "Visualizar": "Visualizar", #usado num elemento especifico por conta do ambiente russo
            "Other Actions": "Otras Acciones",
            "Confirm": "Confirmar",
            "Save": "Grabar",
            "Close": "Finalizar",
            "Exit": "Salir",
            "Leave Page": "Sair da página",
            "Enter": "Entrar",
            "Finish": "Terminar",
            "Details": "Detalles",
            "Search": "Buscar",
            "Ok": "Ok",
            "Copy": "Copiar",
            "Cut": "Recortar",
            "Paste": "Colar",
            "Calculator": "Calculadora",
            "Spool": "Spool",
            "Folders": 'Pastas',
            "Generate Differential File": "Gerar Arquivo Diferencial",
            "Include": "Incluir",
            "Filter": "Filtrar",
			"Menu About": "Ayuda > Sobre",
            "Error Log": "SMARTCLIENT encontrou um problema durante a execucao e sera finalizado. Para informacoes adicionais clique em detalhes",
            "Error Log Print": "SMARTCLIENT encontrou um problema durante a execucao e sera finalizado. Para informacoes adicionais verifique print efetuado da tela",
            "Error Msg Required": "Não é possível completar a ação. Existem campos obrigatórios não preenchidos.",
            "Help": "Ajuda:",
            "Problem": "Problema:",
            "Solution": "Solução:",
            "Branches": "Filiais",
            "Grid Steps Misuse": "Uso de grid errado. Passe apenas um grupo de inputs ou um grupo de checks em cada bloco de grid.",
            "Grid Steps Empty": "Nenhum passo de grid encontrado. Passe um grupo de inputs ou um grupo de checks em cada bloco de grid.",
            "Grid Line Error": "Linha não existe na grid atual.",
            "Grid Column Error": "Coluna não existe na grid atual.",
            "Grid Number Error": "Não existe essa quantidade de grids na tela atual.",
            "Text Not Found": "Texto não encontrado.",
            "Help Not Found": "Help não encontrado.",
            "User Not Authenticated": "Usuário não autenticado",
            "Change Environment": "Trocar módulo",
            "Invert Selection": "Inverte Seleção",
            "Parameter Menu": "Entorno > Archivos > Parametros",
            "Search 2": "Buscar",
            "Search By": "Buscar:",
            "From": "De",
            "To": "Ate",
            "Coins": "Monedas",
            "Next": "Avançar >>",
            "LogOff": "Log Off",
            "Checkhelp": "Help:",
            "Checkproblem": "Problema:",
            "Checksolution": "Solucion:",
            "ChangePassword": "Reserved",
            "UserLogin": "Login del usuario*",
            "CurrentPassword": "Contrasena actual*",
            "NewPassword": "Nueva contrasena*",
            "ConfirmNewPassword": "Confirmar nueva contrasena*",
            "Yes":"Reserved",
            "AssertFalseMessage": "Método AssertFalse utilizado sin un punto de control, verifique el script.",
            "File Name": "Nome do Arquivo",
			"Open": "Abierto",
            "Warning": "Atención",
            "News": "Noticias",
            "Continue": "Continuar",
            "Short Confirm": "Confirmar",
            "Enter in environment screen": "Entrar",
            "Code Coverage": "Aguarde... Coletando informacoes de cobertura de codigo.",
            "Release": "Release",
            "Top DataBase": "Top DataBase",
            "Lib Version": "Versão da lib",
            "Build": "Build",
            "Issued": "Emision",
            "Ref.Dt": "Fc.Ref.",
            "Time": "Hora",
            "End Time": "Hora Término",
            "Procedure Menu": "Base de Dados > Dicionário > Stored Procedure",
            "Code": "Código",
            "Success": "Sucessos",
            "Procedure Install": "Instalar processos selecionados",
            "Procedure Uninstall": "Remover processos selecionados"
        }
        russian = {
            "User": "Пользователь",
            "Password": "Пароль",
            "Database": "Базовая дата",
            "Group": "Группа",
            "Branch": "Филиал",
            "Environment": "Среда",
            "Add": "Добавить",
            "Delete": "Удалить",
            "Edit": "редактировать",
            "Editar": "Изменить", #usado num elemento especifico por conta do ambiente russo
            "Cancel": "Отмена",
            "View": "Просмотр",
            "Visualizar": "Вид...", #usado num elemento especifico por conta do ambiente russo
            #"Other Actions": "Другие Действия",
            "Other Actions": "Др. действия",
            "Confirm": "Подтвердить",
            "Save": "Сохранить",
            "Close": "Закрыть",
            "Exit": "Выход",
            "Leave Page": "Выйти без сохранения",
            "Enter": "Войти",
            "Finish": "Завершить",
            "Details": "Подробнее",
            "Search": "Поиск",
            "Ok": "Да",
            "Copy": "Copy",
            "Cut": "Cut",
            "Paste": "Paste",
            "Calculator": "Calculator",
            "Spool": "Spool",
            "Help": "Help",
            #"Help": "Помощь:",
            "Folders": "Folders",
            "Generate Differential File": "Создать файл изменений",
            "Include": "Bставить",
            "Filter": "фильтр",
            "Menu About": "Справки > О программе…",
            "Error Log": "SMARTCLIENT проблема обнаружена при работе системы, и она будет закрыта. Д/др. инфор-и нажать «Подробности»",
            "Error Log Print": "SMARTCLIENT проблема обнаружена при работе системы, и она будет закрыта.Для получения дополнительной информации проверьте распечатку экрана",
            "Error Msg Required": "Не удалось завершить это действие. Не заполнены обязательные поля.",
            "Problem": "Проблема:",
            "Solution": "Решение:",
            "Branches": "",
            "Grid Steps Misuse": "Grid steps misuse. Be sure to only use a group of inputs or a group of checks in each Grid Block.",
            "Grid Steps Empty": "No grid steps were found. Be sure to only use a group of inputs or a group of checks in each Grid Block.",
            "Grid Line Error": "Line does not exist in current grid.",
            "Grid Column Error": "Column does not exist in current grid.",
            "Grid Number Error": "There is not that many grids on the current screen.",
            "Text Not Found": "Text Not Found",
            "Help Not Found": "Help Not Found",
            "User Not Authenticated": "User Not Authenticated",
            "Change Environment": "Change environment",
            "Invert Selection": "Invert Selection",
            "Parameter Menu": "Среда > НСИ > Параметры",
            "Search 2": "оиск",
            "Search By": "Поиск по:",
            "From": "De",
            "To": "Ate",
            "Coins": "Валюта",
            "Next": "Далее >>",
            "LogOff": "Завершить",
            "Checkhelp": "Помощь:",
            "Checkproblem": "Проблема:",
            "Checksolution": "Решение:",
            "ChangePassword": "Смена пароля",
            "UserLogin": "Пользователь (логин)",
            "CurrentPassword": "Текущий пароль*",
            "NewPassword": "Нов. пароль*",
            "ConfirmNewPassword": "Подтв. новый пароль*",
            "File Name": "имя файла",
			"Open": "открыто",
            "Yes": "Да",
            "AssertFalseMessage": "AssertFalse method used without a checkpoint, check the script.",
            "Warning": "Берегись",
            "News": "Новости",
            "Continue": "Продолжить",
            "Short Confirm": "Подтв.",
            "Enter in environment screen": "Ввод",
            "Code Coverage": "Aguarde... Coletando informacoes de cobertura de codigo.",
            "Release": "Сброс RPO",
            "Top DataBase": "БД",
            "Lib Version": "Версия библиотеки",
            "Build": "Верс.",
            "Issued": "Issued",
            "Ref.Dt": "Ref.Dt",
            "Time": "Time",
            "End Time": "End Time",
            "Procedure Menu": "Database > Dictionary > Stored Procedure",
            "Code": "Код",
            "Success": "успех",
            "Procedure Install": "Установить выбранные процессы",
            "Procedure Uninstall": "Удалить выбранные процессы"
        }

        if language.lower() == "en-us":
            return english
        elif language.lower() == "pt-br":
            return brazilian_portuguese
        elif language.lower() == "ru-ru":
            return russian
        elif language.lower() == "es-es":
            return spanish
        else:
            return brazilian_portuguese

class Messages():

    def __init__(self, languagepack):

        self.grid_misuse = languagepack["Grid Steps Misuse"]
        self.grid_empty = languagepack["Grid Steps Empty"]
        self.grid_line_error = languagepack["Grid Line Error"]
        self.grid_column_error = languagepack["Grid Column Error"]
        self.grid_number_error = languagepack["Grid Number Error"]
        self.error_log = languagepack["Error Log"]
        self.error_log_print = languagepack["Error Log Print"]
        self.error_msg_required = languagepack["Error Msg Required"]
        self.text_not_found = languagepack["Text Not Found"]
        self.user_not_authenticated = languagepack["User Not Authenticated"]
        self.help_not_found = languagepack["Help Not Found"]

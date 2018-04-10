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

        self.error_log = languagepack["Error Log"]
        self.error_log_print = languagepack["Error Log Print"]
        self.error_msg_required = languagepack["Error Msg Required"]
        self.help = languagepack["Help"]
        self.problem = languagepack["Problem"]
        self.solution = languagepack["Solution"]

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
            "Error Msg Required": "This action could not be completed.There are mandatory fields not field.CloseCancel - ",
            "Help": "Help:",
            "Problem": "Problem:",
            "Solution": "Solution:"
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
            "Error Msg Required": "Não é possível completar a ação.Existem campos obrigatórios não preenchidos.FecharCancelar - ",
            "Help": "Ajuda:",
            "Problem": "Problema:",
            "Solution": "Solução:"
        }
        russian = {
            "User": "Пользователь",
            "Password": "Пароль",
            "Database": "Дата",
            "Group": "Группа",
            "Branch": "Филиал",
            "Environment": "Среда",
            "Add": "Добавлять",
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
            "Enter": "Ввод",
            #"Finish": "Завершить",
            "Finish": "3акрыть",
            #"Details": "ДЕТАЛИ",
            "Details": "Подробнее",
            #"Search": "Поиск",
            "Search": "Search",
            "Ok": "Да",
            "Copy": "Copy",
            "Cut": "Cut",
            "Paste": "Paste",
            "Calculator": "Calculator",
            "Spool": "Spool",
            "Help": "Help",
            "Folders": "Folders",
            "Generate Differential File": "Создать файл изменений",
            "Include": "Bставить",
            "Filter": "фильтр",            
            "Menu About": "Справки > О программе…",
            "Error Log": "SMARTCLIENT проблема обнаружена при работе системы, и она будет закрыта. Д/др. инфор-и нажать «Подробности»",
            "Error Log Print": "SMARTCLIENT проблема обнаружена при работе системы, и она будет закрыта.Для получения дополнительной информации проверьте распечатку экрана",
            "Error Msg Required": "Не удалось завершить это действие.Не заполнены обязательные поля.Закрытьотменить - ",
            #"Help": "Помощь:",
            "Problem": "Проблема:",
            "Solution": "Решение:"
        }

        if language.lower() == "en-us": 
            return english
        elif language.lower() == "pt-br":
            return brazilian_portuguese
        elif language.lower() == "ru-ru":
            return russian
        else:
            return brazilian_portuguese
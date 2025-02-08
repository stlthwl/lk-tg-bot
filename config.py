class Message:
    def __init__(self, text):
        self.text = text


class Messages:
    def __init__(self):
        self.messages = {
            'error': Message('Сервис временно недоступен'),
            'select_action': Message('Выберите действие'),
            'email_enter': Message(f'Введите Email, привязанный к профилю ЛК'),
            'email_confirm': Message('На почту отправлено письмо, перейдите по ссылке для подтверждения профиля'),
            'email_not_found': Message('Пользователь с таким Email не найден'),
            'email_not_valid': Message('Невалидная почта, пожалуйста, введите корректный Email'),
            'telegram_not_found': Message('Телеграм не привязан к профилю ЛК'),
            'lk_login': Message('Личный кабинет'),
            'services': Message('Сервисы'),
            'total_appeals': Message('Всего обращений: '),
            'no_rights_appeal_adding': Message('Нет прав на добавление обращений, обратитесь к администритору'),
            'appeal_adding': Message('Чтобы добавить обращение, нажмите кнопку ниже')
        }

    def get_message(self, msg):
        return self.messages.get(msg)


class Button:
    def __init__(self, text, data):
        self.text = text
        self.data = data


class Buttons:
    def __init__(self):
        self.buttons = {
            'appeals': Button('Обращения', 'appeals'),
            'new_appeal': Button('Новое обращение', 'new_appeal'),
            'my_appeals': Button('Мои обращения', 'my_appeals'),
            'lk': Button('servicedesk', {'url': 'https://lk.bingosoft-office.ru/'}),
            'link_telegram': Button('Привязать учетную запись', 'link_telegram'),
            'back_to_start': Button('🔙Назад', '/start'),
            'start': Button('🏚 В начало', '/start'),
            'appeal_adding': Button('Добавить обращение', None)
        }

    def get_button(self, name):
        return self.buttons.get(name)

    def get_appeal_adding_button(self, name, data):
        button = self.buttons.get(name)
        return {
            'text': button.text,
            'web_app': {
                'url': data
            }
        }


class Actions:
    def __init__(self):
        self.actions = None
        self.role_ids = {
            12: {  # Внешний пользователь
                'statuses': {
                    3: [{'name': 'Отозвать обращение', 'procedure_id': 61, 'command_id': 248}],
                    4: [{'name': 'Отозвать обращение', 'procedure_id': 61, 'command_id': 248}],
                    5: [
                        {'name': 'Отозвать обращение', 'procedure_id': 61, 'command_id': 248},
                        {'name': 'Дать уточнение', 'procedure_id': 67, 'command_id': 254}
                    ],
                    6: [{'name': 'Отозвать обращение', 'procedure_id': 61, 'command_id': 248}],
                    7: [{'name': 'Завершить обращение', 'procedure_id': 69, 'command_id': 256}]
                }
            },
            14: {  # Оператор
                'statuses': {
                    3: [
                        {'name': 'Взять обращение на себя', 'procedure_id': 55, 'command_id': 242},
                        {'name': 'Принять в работу', 'procedure_id': 58, 'command_id': 245},
                    ],
                    4: [
                        {'name': 'Взять обращение на себя', 'procedure_id': 55, 'command_id': 242},
                        {'name': 'Принять в работу', 'procedure_id': 58, 'command_id': 245},
                    ],
                    6: [
                        {'name': 'Запросить уточнение у внешнего пользователя', 'procedure_id': 60, 'command_id': 247},
                        {'name': 'Предоставить решение по обращению', 'procedure_id': 80, 'command_id': 261},
                    ]
                }
            }
        }

    def get_available_actions(self, role_id, status_id):
        """ return available actions list """
        if role_id in self.role_ids and status_id in self.role_ids[role_id]['statuses']:
            return self.role_ids[role_id]['statuses'][status_id]
        else:
            return []







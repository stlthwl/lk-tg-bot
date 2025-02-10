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
            'back_to_start': Button('<- Назад', '/start'),
            'start': Button('<<-- В начало', '/start'),
            'appeal_adding': Button('Добавить обращение', None),
            'message_to_user': Button('Сообщение пользователю', 'message_to_user'),
            'message_to_support': Button('Сообщение в поддержку', 'message_to_support')
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
        self.actions = {
            12: [
                {
                    'type': 'appeal',
                    'name': 'Отозвать обращение',
                    'procedure_id': 61,
                    'procedure': 'abandon_appeal_close_status',
                    'params': {
                        'id': 'appeal_id',
                        'user_id': 'user_id',
                        'role_id': 'role_id'
                    },
                    'status_ids': [3, 4, 5, 6]
                },
                {
                    'type': 'event',
                    'name': 'Дать уточнение',
                    'procedure_id': 67,
                    'procedure': 'get_additional_appeal_information',
                    'params': {
                        'id': 'event_id',
                        'user_id': 'user_id'
                    },
                    'status_ids': [5]
                },
                {
                    'type': 'appeal',
                    'name': 'Завершить обращение',
                    'procedure_id': 69,
                    'procedure': 'close_appeal_by_user',
                    'params': {
                        'id': 'appeal_id',
                        'user_id': 'user_id'
                    },
                    'status_ids': [7]
                }
            ],
            14: [
                {
                    'type': 'appeal',
                    'name': 'Взять обращение на себя',
                    'procedure_id': 55,
                    'procedure': 'take_appeal_on_myown',
                    'params': {
                        'id': 'appeal_id',
                        'user_id': 'user_id'
                    },
                    'status_ids': [3, 4]
                },
                {
                    'type': 'appeal',
                    'name': 'Принять в работу',
                    'procedure_id': 58,
                    'procedure': 'take_appeal_into_work',
                    'params': {
                        'id': 'appeal_id',
                        'user_id': 'user_id'
                    },
                    'status_ids': [3, 4]
                },
                {
                    'type': 'event',
                    'name': 'Запросить уточнение',
                    'procedure_id': 60,
                    'procedure': 'additional_appeal_information_for_operator',
                    'params': {
                        'id': 'event_id',
                        'user_id': 'user_id'
                    },
                    'status_ids': [6]
                },
                {
                    'type': 'appeal',
                    'name': 'Предоставить решение',
                    'procedure_id': 80,
                    'procedure': 'finish_appeal_procedure',
                    'params': {
                        'id': 'appeal_id',
                        'user_id': 'user_id',
                        'role_id': 'role_id'
                    },
                    'status_ids': [6]
                }
            ]
        }

    def get_available_actions(self, role_id, status_id):
        """ return available actions list """
        return [i for i in self.actions.get(role_id) if status_id in i.get('status_ids')]

    def get_action_by_procedure_id(self, role_id, procedure_id):
        """ return action """
        return [i for i in self.actions.get(role_id) if procedure_id == i.get('procedure_id')]


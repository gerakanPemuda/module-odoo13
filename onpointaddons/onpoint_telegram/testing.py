import requests


def send_message(text):
    token = '1755390496:AAF40j0iNVXU2F_vHvSffia4skxvQhkJe2o'
    chat_id = "-427879581"
    url_req = "https://api.telegram.org/bot" + token + "/sendMessage" + "?chat_id=" + chat_id + '&text=' + text
    results = requests.get(url_req)
    print(results.json())


send_message("hello group 3\nTES ENTER")

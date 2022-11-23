# '''!/usr/bin/env python3'''
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : https://github.com/renanrrodrigues
# Email: contatorenanrrodrigues@gmail.com
# Created Date: 18/11/2022 05:52
# version ='1.0'
# ---------------------------------------------------------------------------
""" rpa pipefy """
import datetime
# ---------------------------------------------------------------------------
# Imports Line
# ---------------------------------------------------------------------------
import json
import os
import sys
import time
import requests
from loguru import logger
from termcolor import RESET
from os import system, name
import secrets

# -------Static variables--------------------------------------------------------------------

URL_API = "https://app.pipefy.com/graphql"
logger.add("file.log", format="\n--------------------- log {time} ---------------------\n{level}\n{message}\nLINHA:{line}", filter="__main__", level="INFO")

list_done = []
list_failed = []
'''
logger.debug('Debug')
logger.info('Info')
logger.warning('Warning')
logger.error('Error')
logger.critical('Critical')
'''


# ---------------------------------------------------------------------------


class OpenFile:
    """
        Classe retorna arquivo de configuração dict config.json
    """

    def __init__(self, file):
        self.file = file

    def open_file(self):
        """
            Entry:
            método recebe o caminho do arquivo de configuração..
            ex: 'C:\rpa_pipefy\config.json'
            ex: 'config.json' na raiz do main.py

            Return:
            retorna um DICT com os dados de configuração.
        """
        try:
            f = open(self.file)
            data_file = json.load(f)
            return data_file
        except Exception:
            logger.critical('Error: Não foi possível carregar o arquivo de configuração!')
            quit()


class RequestApi:
    """
    return response request
    """

    def __init__(self, url, payload, headers):
        self.url = url
        self.payload = payload
        self.headers = headers

    def return_requests(self):
        """
            método que retorna um response da API.
            passamos como argumento a rota, payload e headers.
            em nosso caso estamos requisitando de uma API em GraphQL em tão é tudo POST
            # referência em --> https://graphql.org/learn/serving-over-http/
        """
        try:
            response = requests.post(self.url, json=self.payload, headers=self.headers)

            if response.status_code == 200:
                return response
            else:
                logger.warning(f'warning! status code: {response.status_code}')
                return False
        except requests.exceptions.HTTPError:
            logger.error('Http Error:')
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Error Connecting:")
            return False
        except requests.exceptions.Timeout:
            logger.error("Timeout Error:")
            return False
        except requests.exceptions.RequestException:
            logger.error("OOps: Something Else")
            return False


class ExportPipeReportId:
    """
        return exportPipeReport or false
    """

    def __init__(self, pipe_id, pipe_report_id, token):
        self.id_pipe = pipe_id
        self.pipe_report_id = pipe_report_id
        self.token = token

    def export_pipe_report(self):
        """
        doc pipefy https://developers.pipefy.com/reference/pipe-reports#exportpipereport-mutation
        método que gera um novo relatório, e retorna o id do mesmo.

        """
        payload = {
            "query": "mutation {\n  exportPipeReport(input: {pipeId: "f'{int(self.id_pipe)}'", pipeReportId: "f'{int(self.pipe_report_id)}'"}) {\n    pipeReportExport {\n      id\n    }\n  }\n}",
            "variables": None
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer "f'{self.token}'""
        }
        try:
            response = RequestApi(URL_API, payload, headers).return_requests()
            if response is not False:  # verifica se obteve um response valido
                response = response.json()
                if response['data']['exportPipeReport'] is not None:  # verifica se o exportPipeReport não está vazio
                    return response['data']['exportPipeReport']['pipeReportExport']['id']
                else:
                    if 'errors' in response:  # se está vazio provavelmente deu erro
                        logger.warning(
                            f"Warning: Esse relatório ({self.pipe_report_id}) falhou!\n{response['errors'][0]['message']}")
                        return False
                    else:
                        logger.error(f'Esse relatório falhou!\nAlgo está errado com a requisição na API.')
                        return False
            else:
                logger.error('Esse relatório falhou!\nAlgo está errado com a requisição na API.')
                return False
        except Exception:
            logger.critical(f'Erro interno no método que gera id do relatório!!')
            quit()


class PipeReportExportLink:
    """
    doc pipefy https://developers.pipefy.com/reference/pipe-reports#exportpipereport-mutation
    function return [link, name_report] or bool
    """

    def __init__(self, id_pipe_report_export, pipe_id, report_id, token):
        self.id_pipe_report_export = id_pipe_report_export
        self.pipe_id = pipe_id
        self.report_id = report_id
        self.token = token

    def filter_data_query(self, data):
        """
        return query
        método filtra o retorno da requisição, pegando link do relatório e nome do relatório
        """
        try:
            link = data['data']['pipeReportExport']['fileURL']
            file_name = data['data']['pipe']['reports']
            for x in file_name:  # for itera todos os relatórios do pipe até encontrar o que está sendo passado, para conseguir o nome do mesmo.
                if int(x['id']) == self.report_id:
                    return [link, x['name']]
        except Exception:
            logger.critical(
                f'Erro interno na função que filtra o retorno da requisição "pipeReportExport"! {Exception} \n\n{data}\n\n')
            quit()

    def pipe_report_export(self):
        """

        """
        payload = {
            "query": "{\n  pipeReportExport(id: "f'{int(self.id_pipe_report_export)}'") {\n    fileURL\n    state\n    startedAt\n    requestedBy {\n      id\n    }\n  }\n  pipe(id:"f'{int(self.pipe_id)}'"){\n   reports{\n    id\n    name\n  }\n  }\n}",
            "variables": None
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer "f'{self.token}'""
        }
        try:
            response = RequestApi(URL_API, payload, headers).return_requests()

            if response is not False:
                response = response.json()
                if response['data']['pipeReportExport'] is not None:
                    return PipeReportExportLink(self.id_pipe_report_export, self.pipe_id, self.report_id,
                                                self.token).filter_data_query(
                        response)  # return response['data']['pipeReportExport']['fileURL']
                elif 'errors' in response:
                    logger.warning(
                        f"Warning: Esse relatório ({self.report_id}) falhou!\n{response['errors'][0]['message']}")
                    return False
                else:
                    logger.warning(
                        f'Warning: Esse relatório ({self.report_id}) falhou! Não foi possível obter o link do relatório!')
                    return False
            else:
                logger.error(f'Esse relatório falhou!\nAlgo está errado com a requisição na API. {response}')
                return False
        except Exception:
            logger.critical(f'Erro interno no método que gera link do relatorio! {Exception}')
            quit()


class SaveReportFile:
    """
    save file report
    """

    def __init__(self, link_report, save_path, name_file, backup_status):
        self.link_report = link_report
        self.save_path = save_path
        self.name_file = name_file
        self.backup_status = backup_status

    def check_file_backup(self):
        try:
            if self.backup_status:
                if os.path.isfile(f'{self.save_path}\\{self.name_file}.xlsx'):
                    return True
                else:
                    return False
            else:
                return False
        except Exception:
            logger.critical(f'erro interno no método check_file_backup:\nnão foi possível modificar o arquivo do relatório ({self.save_path}) \n{Exception}\n')
            quit()

    def check_folder(self):

        try:
            if os.path.exists(self.save_path):
                return True
            else:
                os.mkdir(self.save_path)
                return True
        except Exception:
            logger.critical(f'não foi possível verificar o diretorio ({self.save_path}) \n{Exception}\n')
            quit()

    def backup_file(self):
        try:
            secret = secrets.token_urlsafe(16)
            code_file = f'{secret[0:6]}'
            if os.path.exists(f'{self.save_path}\\BACKUP-{self.name_file}'):
                # using os.rename() method
                os.rename(f'{self.save_path}\\{self.name_file}.xlsx', f'{self.save_path}\\BACKUP-{self.name_file}\\BK-{code_file}-{self.name_file}.xlsx')
                return True
            else:
                os.mkdir(f'{self.save_path}\\BACKUP-{self.name_file}')
                time.sleep(1)
                os.rename(f'{self.save_path}\\{self.name_file}.xlsx', f'{self.save_path}\\BACKUP-{self.name_file}\\BK-{code_file}-{self.name_file}.xlsx')
                return True
        except Exception:
            logger.critical(f'não foi possível fazer um backup do arquivo ({self.save_path}\\{self.name_file}) \n{Exception}\n')
            quit()

    def download_save(self):
        """
                    verifica se a pasta existe
                    return bool
        """
        try:
            if self.check_folder():  # verifica se a pasta existe!
                path_file = f'{self.save_path}\\{self.name_file}.xlsx'
                if self.check_file_backup():
                    if self.backup_file():
                        with open(path_file, "wb") as f:
                            response = requests.get(self.link_report, stream=True)
                            total_length = response.headers.get('content-length')

                            if total_length is None:  # no content length header
                                f.write(response.content)
                            else:
                                dl = 0
                                total_length = int(total_length)
                                for data in response.iter_content(chunk_size=total_length):
                                    dl += len(data)
                                    f.write(data)
                                    done = int(24 * dl / total_length)
                                    sys.stdout.write(
                                        "\r\033[0;32m[%s%s\033[0;32m]" % ('\033[1;31m=' * done, ' ' * (24 - done)))
                                    sys.stdout.flush()
                                sys.stdout.write(' Download --> 100%')
                                sys.stdout.write(RESET)
                        print(
                            f'\n\033[1;36m relatório ({self.name_file}) 💾 salvo em --> {self.save_path}\\{self.name_file}.xlsx')
                        sys.stdout.write(RESET)
                        return True
                    else:
                        logger.critical(f'não foi possível fazer um backup do arquivo ({self.save_path}\\{self.name_file}) \n{Exception}\n')
                        quit()
                else:
                    with open(path_file, "wb") as f:
                        response = requests.get(self.link_report, stream=True)
                        total_length = response.headers.get('content-length')

                        if total_length is None:  # no content length header
                            f.write(response.content)
                        else:
                            dl = 0
                            total_length = int(total_length)
                            for data in response.iter_content(chunk_size=total_length):
                                dl += len(data)
                                f.write(data)
                                done = int(24 * dl / total_length)
                                sys.stdout.write("\r\033[0;32m[%s%s\033[0;32m]" % ('\033[1;31m=' * done, ' ' * (24 - done)))
                                sys.stdout.flush()
                            sys.stdout.write(' Download --> 100%')
                            sys.stdout.write(RESET)
                    print(
                        f'\n\033[1;36m relatório ({self.name_file}) 💾 salvo em --> {self.save_path}\\{self.name_file}.xlsx')
                    sys.stdout.write(RESET)
                    return True
            else:
                return False
        except Exception:
            logger.critical('erro interno no método download_save!')
            quit()


# define our clear function
def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')


def worker_report(report_item):
    print('\n')
    requesting_new_report = ExportPipeReportId(report_item['pipe_id'], report_item['report_id'],
                                               token_api).export_pipe_report()  # pode retornar int ou bool

    if type(requesting_new_report) != bool:  # requesting_report retorna False se ocorreu algum erro.
        link_name_report = PipeReportExportLink(int(requesting_new_report), report_item['pipe_id'],
                                                report_item['report_id'],
                                                token_api).pipe_report_export()

        if type(link_name_report) != bool and link_name_report is not None:
            print(f"📊 relatório ({link_name_report[1]}) gerado com sucesso!")
            time.sleep(0.2)
            print(f"🤖 baixando relatório --> ({link_name_report[1]})")

            # baixando e salvando file !!!!!!
            if SaveReportFile(link_name_report[0], report_item['save_path'], link_name_report[1], report_item['backup_file']).download_save():
                list_done.append(item)
            else:
                logger.warning(f"o download desse relatório ({report_item['report_id']}) falhou!")

        else:
            print(f"link para download desse relatório ({report_item['report_id']}) falhou!")
    else:
        list_failed.append(item)
    time.sleep(0.8)


if __name__ == '__main__':
    logger.info(f'\n\n--------------------- start {datetime.datetime.now()} ---------------------')
    """
    permissões...
    https://help.pipefy.com/pt-BR/articles/6027079-funcoes-e-permissoes-da-empresa
    
    
    Rate Limits: rate limit is 25 requests in 24 hours, for each pipe.
    https://developers.pipefy.com/reference/pipe-reports#export-report
    
    
    Chamadas de API -->  Starter:20 | Business:500 | Enterprise:10.000
    https://www.pipefy.com/pt-br/precos/?ref=app
    """

    clear()
    print('🤖 configurando automação...')
    time.sleep(1.5)
    # ------------------------------------------- CONFIG ---------------------------------
    config = OpenFile('config.json').open_file()
    reports = len(config['reports'])
    token_api = config['token']
    time.sleep(1.5)
    print(f'\nconfiguração concluída. --> {config["config_name"]}')

    # ------------------------------------------------ CONFIG -------------------------------------

    # método que gera um novo relatório, e retorna o número do relatório gerado, mutation
    time.sleep(2.5)
    clear()
    print(f'\nnúmero de relatórios: {reports}')

    for item in config['reports']:  # itera todos os relatórios criados no arquivo config
        if item['active']:
            worker_report(item)
            time.sleep(2.4)
    print(f'\n\nnúmero de relatórios que falharam!:--> {len(list_failed)}')

    list_failed_freeze = list_failed
    list_failed = []
    # tentando novamente os relatórios que falharam...
    if len(list_failed_freeze) >= 1:
        print('tentando novamente...')
        for item_failed in list_failed_freeze:
            worker_report(item_failed)
            time.sleep(2.6)
    print(
        f'\n\n\n🚀 \033[0;35mrpa finalizado com sucesso!\n\n📊 \033[0;32mrelatórios salvos com sucesso: {len(list_done)}\033[0;0m\n⛔ \033[1;31mrelatórios com falhas: {len(list_failed)}\033[0;0m\n\n')

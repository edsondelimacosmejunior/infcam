import os
import requests
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .models import Profile
from odoo.models import Odoo
from odoo.models import OdooParceiro
from odoo.api_client.parceiro import get_parceiro, get_id_parceiro, criar_parceiro
from odoo.api_client.reparo import get_reparo, get_reparos, get_ultimos_reparos, criar_reparo, get_reparos_tecnico, alterar_estagio_reparo
from odoo.api_client.anexo import criar_anexo
from odoo.api_client.produto import get_produtos
from odoo.api_client.produto import get_produto
from odoo.api_client.produto_reparo import criar_produto_reparo
from odoo.api_client.servico_reparo import criar_servico_reparo
from odoo.api_client.reparo import adicionar_laudo_reparo
from odoo.api_client.nota import criar_nota


# Create your views here.
def validar_acesso(funcao):
    def validar(*args, **kwargs):
        if args[0].user.has_perm('helpdesk.tecnico_infcam'):
            return redirect(reverse_lazy('dashboard_tecnico'))
        else:
            parceiro = OdooParceiro.objects.filter(user=args[0].user.id).first()

            odoo = Odoo.objects.get(id=1)
            models = odoo.conectar()

            if not parceiro:
                return redirect(reverse_lazy('vincular_usuario'))

            return funcao(
                *args,
                **kwargs,
                parceiro=parceiro,
                odoo=odoo,
                models=models
            )
    return validar


@login_required
def vincular_usuario(request):
    if request.method == 'POST':
        email = request.POST.get('email', None)

        odoo = Odoo.objects.get(id=1)
        models = odoo.conectar()

        if email:
            parceiro = get_id_parceiro(odoo, models, email)

            if parceiro:
                odoo_parceiro = OdooParceiro(user=request.user, id_parceiro=parceiro['id'])
                odoo_parceiro.save()

                data = {
                    'encontrado': True,
                    'resposta': 'Cliente encontrado: ' + parceiro['name']
                }
            else:
                data = {
                    'encontrado': False,
                    'resposta': 'Cliente não encontrado, pesquise novamente!'
                }
            return JsonResponse(data)
        else:
            return render(request, 'usuario/index.html')
    else:
        return render(request, 'usuario/index.html')

@login_required
def criar_usuario(request):
    if request.method == 'POST':
        nome = request.POST.get('nome', None)
        pessoa_fisica_juridica = request.POST.get('pessoa_fisica_juridica', None)
        cpf_cnpj = request.POST.get('cpf_cnpj', None)
        celular = request.POST.get('celular', None)
        email = request.POST.get('email', None)

        odoo = Odoo.objects.get(id=1)
        models = odoo.conectar()

        parceiro = get_id_parceiro(odoo, models, email)

        if parceiro:
            try:
                odoo_parceiro = OdooParceiro(user=request.user, id_parceiro=parceiro['id'])
                odoo_parceiro.save()
                data = {
                    'encontrado': True,
                    'resposta': 'Cliente encontrado: ' + parceiro['name']
                }
            except:
                data = {
                    'encontrado': False,
                    'resposta': 'Erro ao criar usuário, entre em contato com o administrado!'
                }
        else:
            id_parceiro = criar_parceiro(odoo, models, nome, pessoa_fisica_juridica, cpf_cnpj, celular, email)
            if id_parceiro:
                odoo_parceiro = OdooParceiro(user=request.user, id_parceiro=id_parceiro)
                odoo_parceiro.save()
                data = {
                    'encontrado': True,
                    'resposta': 'Cadastrado com sucesso!'
                }
            else:
                data = {
                    'encontrado': False,
                    'resposta': 'Erro ao criar usuário, entre em contato com o administrado!'
                }
        return JsonResponse(data)
    else:
        return render(request, 'usuario/novo_parceiro.html',{'title': 'Criar Usuário'})


@login_required
@validar_acesso
def dashboard_cliente(request, parceiro, odoo, models):
    ultimos_reparos = get_ultimos_reparos(odoo, models, parceiro.id_parceiro)
    return render(
        request,
        'dashboard/cliente.html',
        {
            'title': 'Dashboard',
            'parceiro': parceiro,
            'ultimos_reparos': ultimos_reparos
        }
    )


@login_required
def dashboard_tecnico(request):
    if not request.user.has_perm('helpdesk.tecnico_infcam'):
        return HttpResponseForbidden()
    else:
        odoo = Odoo.objects.get(id=1)
        models = odoo.conectar()

        meus_reparos = get_reparos_tecnico(odoo, models, request.user.profile.res_user)

        return render(
            request,
            'dashboard/tecnico.html',
            {
                'title': 'Dashboard',
                'ultimos_reparos': meus_reparos
            }
        )


@login_required
def detalhar_reparo(request, reparo):
    if not request.user.has_perm('helpdesk.tecnico_infcam'):
        return HttpResponseForbidden()
    else:
        odoo = Odoo.objects.get(id=1)
        models = odoo.conectar()

        reparo = get_reparo(odoo, models, reparo)

        return render(
            request,
            'reparo/detalhe.html',
            {
                'title': 'Detalhar Reparo',
                'reparo': reparo
            }
        )


@login_required
def adicionar_anexo(request, reparo):
    import base64
    if not request.user.has_perm('helpdesk.tecnico_infcam'):
        return HttpResponseForbidden()
    else:
        if request.method == 'POST':
            #try:
            odoo = Odoo.objects.get(id=1)
            models = odoo.conectar()

            anexo = request.FILES.get('anexo', None)
            observacao = request.POST.get('observacao', None)

            anexo_comprimido = comprimir_imagem(anexo)

            anexo_base_64 = base64.b64encode(anexo_comprimido).decode('utf-8')
            nome_anexo = "{}{}".format(observacao, os.path.splitext(str(anexo))[1])
            anexo_odoo = criar_anexo(odoo, models, nome_anexo, anexo_base_64, anexo.content_type, 'mrp.repair', reparo)
            if anexo_odoo:
                return redirect(reverse_lazy('detalhar_reparo', kwargs={'reparo': reparo}))
            else:
                return render(
                    request,
                    'reparo/adicionar_anexo.html',
                    {
                        'title': 'Adicionar Anexo',
                        'reparo': reparo,
                        'erro': 'Erro ao anexar imagem, contacte o administrador!'
                    }
                )
            #except:
            #    return render(
            #        request,
            #        'reparo/adicionar_anexo.html',
            #        {
            #            'title': 'Adicionar Anexo',
            #            'reparo': reparo,
            #            'erro': 'Erro ao anexar imagem, contacte o administrador!'
            #        }
            #    )
        else:
            return render(
                request,
                'reparo/adicionar_anexo.html',
                {
                    'title': 'Adicionar Anexo',
                    'reparo': reparo
                }
            )


@login_required
def alterar_estagio(request, reparo):
    if not request.user.has_perm('helpdesk.tecnico_infcam'):
        return HttpResponseForbidden()
    else:
        if request.method == 'POST':
            try:
                odoo = Odoo.objects.get(id=1)
                models = odoo.conectar()

                estagio = request.POST.get('estagio', None)
                obj_reparo = get_reparo(odoo, models, reparo)

                usuarios_habilitados = OdooParceiro.objects.filter(id_parceiro=obj_reparo['partner_id'][0])

                assinatura_validada = True

                if assinatura_validada:        
                    mudanca = alterar_estagio_reparo(odoo, models, reparo, estagio)
                    if mudanca:
                        return redirect(reverse_lazy('detalhar_reparo', kwargs={'reparo': reparo}))
                    else:
                        return render(
                            request,
                            'reparo/alterar_estagio.html',
                            {
                                'title': 'Alterar Estágio',
                                'reparo': reparo,
                                'erro': 'Erro ao alterar estágio, contacte o administrador!'
                            }
                        )
                else:
                    return render(
                            request,
                            'reparo/alterar_estagio.html',
                            {
                                'title': 'Alterar Estágio',
                                'reparo': reparo,
                                'erro': 'Assinatura não validada!'
                            }
                        )
            except:
                return render(
                    request,
                    'reparo/alterar_estagio.html',
                    {
                        'title': 'Alterar Estágio',
                        'reparo': reparo,
                        'erro': 'Erro ao alterar estágio, contacte o administrador!'
                    }
                )
        else:
            return render(
                request,
                'reparo/alterar_estagio.html',
                {
                    'title': 'Alterar Estágio',
                    'reparo': reparo,
                }
            )


@login_required
def fechar_os(request, reparo):
    if not request.user.has_perm('helpdesk.tecnico_infcam'):
        return HttpResponseForbidden()
    else:
        if request.method == 'POST':
            try:
                odoo = Odoo.objects.get(id=1)
                models = odoo.conectar()

                estagio = request.POST.get('estagio', None)
                qrcode = request.POST.get('qrcode', None)
                obj_reparo = get_reparo(odoo, models, reparo)

                usuarios_habilitados = OdooParceiro.objects.filter(id_parceiro=obj_reparo['partner_id'][0])

                assinatura_validada = False
                for usuario in usuarios_habilitados:
                    if usuario.user.password == qrcode:
                        assinatura_validada = True

                if assinatura_validada:        
                    mudanca = alterar_estagio_reparo(odoo, models, reparo, estagio)
                    if mudanca:
                        return redirect(reverse_lazy('detalhar_reparo', kwargs={'reparo': reparo}))
                    else:
                        return render(
                            request,
                            'reparo/alterar_estagio.html',
                            {
                                'title': 'Alterar Estágio',
                                'reparo': reparo,
                                'erro': 'Erro ao alterar estágio, contacte o administrador!'
                            }
                        )
                else:
                    return render(
                            request,
                            'reparo/fechar_os.html',
                            {
                                'title': 'Fechar OS',
                                'reparo': reparo,
                                'erro': 'Assinatura não validada!'
                            }
                        )
            except:
                return render(
                    request,
                    'reparo/fechar_os.html',
                    {
                        'title': 'Fechar OS',
                        'reparo': reparo,
                        'erro': 'Erro ao alterar estágio, contacte o administrador!'
                    }
                )
        else:
            return render(
                request,
                'reparo/fechar_os.html',
                {
                    'title': 'Fechar OS',
                    'reparo': reparo,
                }
            )


@login_required
def adicionar_produto(request, reparo):
    if not request.user.has_perm('helpdesk.tecnico_infcam'):
        return HttpResponseForbidden()
    else:
        if request.method == 'POST':
            try:
                odoo = Odoo.objects.get(id=1)
                models = odoo.conectar()

                produto = request.POST.get('produto', None)
                quantidade = request.POST.get('quantidade', None)
                observacao = request.POST.get('observacao', None)

                obj_produto = get_produto(odoo, models, produto)
                produto_reparo = criar_produto_reparo(odoo, models, produto, observacao, obj_produto['uom_id'][0], obj_produto['list_price'], quantidade, reparo)

                if produto_reparo:
                    return redirect(reverse_lazy('detalhar_reparo', kwargs={'reparo': reparo}))
                else:
                    produtos = get_produtos(odoo, models ,tipo=['product'])
                    return render(
                        request,
                        'reparo/adicionar_produto.html',
                        {
                            'title': 'Adicionar Produto',
                            'reparo': reparo,
                            'produtos': produtos,
                            'erro': 'Erro ao adicionar produto, contacte o administrador!'
                        }
                    )
            except:
                produtos = get_produtos(odoo, models ,tipo=['product'])
                return render(
                    request,
                    'reparo/adicionar_produto.html',
                    {
                        'title': 'Adicionar Produto',
                        'reparo': reparo,
                        'produtos': produtos,
                        'erro': 'Erro ao adicionar produto, contacte o administrador!'
                    }
                )
        else:
            odoo = Odoo.objects.get(id=1)
            models = odoo.conectar()
            produtos = get_produtos(odoo, models, tipo=['product'])

            return render(
                request,
                'reparo/adicionar_produto.html',
                {
                    'title': 'Adicionar Produto',
                    'reparo': reparo,
                    'produtos': produtos
                }
            )


@login_required
def adicionar_servico(request, reparo):
    if not request.user.has_perm('helpdesk.tecnico_infcam'):
        return HttpResponseForbidden()
    else:
        if request.method == 'POST':
            try:
                odoo = Odoo.objects.get(id=1)
                models = odoo.conectar()

                produto = request.POST.get('produto', None)
                quantidade = request.POST.get('quantidade', None)
                observacao = request.POST.get('observacao', None)

                obj_produto = get_produto(odoo, models, produto)
                servico_reparo = criar_servico_reparo(odoo, models, produto, observacao, obj_produto['uom_id'][0], obj_produto['list_price'], quantidade, reparo)

                if servico_reparo:
                    return redirect(reverse_lazy('detalhar_reparo', kwargs={'reparo': reparo}))
                else:
                    produtos = get_produtos(odoo, models, tipo=['service'])
                    return render(
                        request,
                        'reparo/adicionar_servico.html',
                        {
                            'title': 'Adicionar Serviço',
                            'reparo': reparo,
                            'produtos': produtos,
                            'erro': 'Erro ao adicionar serviço, contacte o administrador!'
                        }
                    )
            except:
                produtos = get_produtos(odoo, models, tipo=['service'])
                return render(
                    request,
                    'reparo/adicionar_servico.html',
                    {
                        'title': 'Adicionar Serviço',
                        'reparo': reparo,
                        'produtos': produtos,
                        'erro': 'Erro ao adicionar serviço, contacte o administrador!'
                    }
                )
        else:
            odoo = Odoo.objects.get(id=1)
            models = odoo.conectar()
            produtos = get_produtos(odoo, models, tipo=['service'])

            return render(
                request,
                'reparo/adicionar_servico.html',
                {
                    'title': 'Adicionar Serviço',
                    'reparo': reparo,
                    'produtos': produtos
                }
            )


@login_required
def adicionar_laudo(request, reparo):
    if not request.user.has_perm('helpdesk.tecnico_infcam'):
        return HttpResponseForbidden()
    else:
        if request.method == 'POST':
            try:
                odoo = Odoo.objects.get(id=1)
                models = odoo.conectar()

                laudo = request.POST.get('laudo', None)

                obj_reparo = get_reparo(odoo, models, reparo)
                texto_laudo = "{} / {}".format(obj_reparo['quotation_notes'], laudo)
                laudo_reparo = adicionar_laudo_reparo(odoo, models, texto_laudo, reparo)

                if laudo_reparo:
                    return redirect(reverse_lazy('detalhar_reparo', kwargs={'reparo': reparo}))
                else:
                    return render(
                        request,
                        'reparo/adicionar_laudo.html',
                        {
                            'title': 'Adicionar Laudo',
                            'reparo': reparo,
                            'erro': 'Erro ao adicionar laudo, contacte o administrador!'
                        }
                    )
            except:
                return render(
                    request,
                    'reparo/adicionar_laudo.html',
                    {
                        'title': 'Adicionar Laudo',
                        'reparo': reparo,
                        'erro': 'Erro ao adicionar laudo, contacte o administrador!'
                    }
                )
        else:
            return render(
                request,
                'reparo/adicionar_laudo.html',
                {
                    'title': 'Adicionar Laudo',
                    'reparo': reparo
                }
            )



@login_required
@validar_acesso
def novo_reparo(request, parceiro, odoo, models):
    if request.method == 'POST':
        produto = request.POST.get('produto', None)
        descricao = request.POST.get('descricao', None)

        reparo = criar_reparo(odoo, models, parceiro.id_parceiro, produto, descricao)

        if reparo:
            return redirect(reverse_lazy('dashboard_cliente'))
        else:
            return render(
                request,
                'reparo/novo.html',
                {
                    'title': 'Novo Reparo',
                    'parceiro': parceiro,
                    'erro': 'Erro ao cadastrar, tente novamente mais tarde!'
                }
            )
    else:
        return render(
            request,
            'reparo/novo.html',
            {
                'title': 'Novo Reparo',
                'parceiro': parceiro
            }
        )


@login_required
def adicionar_nota(request, reparo):
    if not request.user.has_perm('helpdesk.tecnico_infcam'):
        return HttpResponseForbidden()
    else:
        if request.method == 'POST':
            odoo = Odoo.objects.get(id=1)
            models = odoo.conectar()
            
            nota = request.POST.get('nota', None)
            nota = criar_nota(odoo, models, reparo, nota)

            if nota:
                return redirect(reverse_lazy('detalhar_reparo', kwargs={'reparo': reparo}))
            else:
                return render(
                    request,
                    'reparo/adicionar_nota.html',
                    {
                        'title': 'Nova Nota',
                        'reparo': reparo,
                        'erro': 'Erro ao cadastrar, tente novamente mais tarde!'
                    }
                )
        else:
            return render(
                request,
                'reparo/adicionar_nota.html',
                {
                    'title': 'Nova Nota',
                    'reparo': reparo
                }
            )


@login_required
@validar_acesso
def dados_pessoais(request, parceiro, odoo, models):
    pessoa = get_parceiro(odoo, models, parceiro.id_parceiro)

    return render(
        request,
        'dados_pessoais/index.html',
        {
            'title': 'Dados Pessoais',
            'parceiro': parceiro,
            'pessoa': pessoa
        }
    )


@login_required
@validar_acesso
def qr_code(request, parceiro, odoo, models):
    usuario = request.user

    return render(
        request,
        'usuario/qr_code.html',
        {
            'title': 'QR Code',
            'usuario': usuario
        }
    )


def comprimir_imagem(arquivo):
    from PIL import Image
    import io

    imagem = Image.open(arquivo.file)

    imagem_comprimida = imagem.resize((int(imagem.width*0.5), int(imagem.height*0.5)), Image.ANTIALIAS)

    img_byte_array = io.BytesIO()

    imagem_comprimida.save(img_byte_array, format=imagem.format)

    img_byte_array = img_byte_array.getvalue()
    return img_byte_array

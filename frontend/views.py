from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.contrib.auth.models import User  # Use o modelo padrão do Django


# ---------------------------
# Login personalizado
# ---------------------------
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        return '/'

    def form_invalid(self, form):
        messages.error(self.request, "❌ Email ou senha incorretos.")
        return super().form_invalid(form)


# ---------------------------
# Cadastro de usuário
# ---------------------------
class CadastroView(View):
    template_name = 'registration/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')  # Mude de 'nome' para 'username'
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validações
        if not all([username, email, password1, password2]):
            messages.error(request, "❌ Todos os campos são obrigatórios.")
            return redirect('cadastro')

        if password1 != password2:
            messages.error(request, "❌ As senhas não coincidem.")
            return redirect('cadastro')

        if User.objects.filter(email=email).exists():
            messages.error(request, "⚠️ Este email já está em uso.")
            return redirect('cadastro')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "⚠️ Este nome de usuário já está em uso.")
            return redirect('cadastro')

        # Criação do usuário usando o modelo padrão do Django
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=username.split()[0] if username.split() else username  # Pega primeiro nome
            )

            # Login automático
            user = authenticate(request, username=username, password=password1)
            if user:
                login(request, user)
                messages.success(request, f"🎉 Bem-vindo(a), {username}!")
                return redirect('home')
            else:
                messages.error(request, "❌ Erro ao autenticar automaticamente.")
                return redirect('login')

        except Exception as e:
            messages.error(request, f"❌ Erro ao criar usuário: {e}")
            return redirect('cadastro')


# ---------------------------
# Página de configurações
# ---------------------------
@login_required
def configuracoes_view(request):
    return render(request, 'configuracoes.html')


# ---------------------------
# Logout
# ---------------------------
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "👋 Você saiu com sucesso!")
    return redirect('login')


@login_required
def alterar_senha(request):
    if request.method == 'POST':
        senha_atual = request.POST.get('senha_atual')
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')
        
        # Validações
        if not request.user.check_password(senha_atual):
            messages.error(request, "❌ Senha atual incorreta.")
            return redirect('configuracoes')
        
        if nova_senha != confirmar_senha:
            messages.error(request, "❌ As novas senhas não coincidem.")
            return redirect('configuracoes')
        
        if len(nova_senha) < 6:
            messages.error(request, "❌ A senha deve ter pelo menos 6 caracteres.")
            return redirect('configuracoes')
        
        # Alterar senha
        try:
            request.user.set_password(nova_senha)
            request.user.save()
            # Re-autenticar o usuário após mudança de senha
            user = authenticate(request, username=request.user.username, password=nova_senha)
            if user:
                login(request, user)
            messages.success(request, "✅ Senha alterada com sucesso!")
            return redirect('configuracoes')
        except Exception as e:
            messages.error(request, f"❌ Erro ao alterar senha: {e}")
            return redirect('configuracoes')
    
    return redirect('configuracoes')
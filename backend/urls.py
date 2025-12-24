from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from frontend.views import configuracoes_view, CustomLoginView, CadastroView, logout_view, alterar_senha

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.home.urls')),
    path('crm/', include('apps.crm.urls')),
    path('calendario/', include(('apps.calendario.urls', 'calendario'), namespace='calendario')),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('cadastro/', CadastroView.as_view(), name='cadastro'),
    path('configuracoes/', configuracoes_view, name='configuracoes'),
    path('alterar-senha/', alterar_senha, name='alterar_senha'),
]
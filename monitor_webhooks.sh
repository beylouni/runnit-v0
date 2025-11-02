#!/bin/bash

API_URL="https://garmin-integration-api.onrender.com"

echo "🔍 MONITORAMENTO DE WEBHOOKS E DADOS"
echo "===================================="
echo ""
echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

echo "1️⃣ Status da API:"
curl -s ${API_URL}/health | jq .
echo ""

echo "2️⃣ Estatísticas de Atividades:"
curl -s ${API_URL}/data/activities/stats | jq .
echo ""

echo "3️⃣ Últimas 3 Atividades:"
curl -s "${API_URL}/data/activities?limit=3" | jq '.activities[] | {id: .garmin_activity_id, name: .activity_name, sport: .sport, start_time: .start_time}'
echo ""

echo "4️⃣ Usuários:"
curl -s ${API_URL}/data/users | jq '.users[] | {id: .garmin_user_id, email: .email, name: .name}'
echo ""

echo "✅ Monitoramento concluído!"
echo ""
echo "💡 O QUE ESPERAR:"
echo "   → Garmin envia webhooks automaticamente quando:"
echo "      • Nova atividade é registrada"
echo "      • Dados de saúde são sincronizados"
echo "      • Relógio sincroniza com app Garmin Connect"
echo ""
echo "   → Primeiros webhooks após autenticação:"
echo "      • userPermissionsChange: confirmação de permissões (já recebido!)"
echo "      • dailies: dados de saúde diários"
echo "      • activities: próxima atividade que você fizer"
echo ""
echo "📱 Para testar imediatamente:"
echo "   → Abra o app Garmin Connect no celular"
echo "   → Force uma sincronização manual"
echo "   → Aguarde 1-2 minutos"
echo "   → Execute este script novamente"
echo ""
echo "🏃 Ou faça uma atividade curta:"
echo "   → Comece uma corrida/caminhada no relógio"
echo "   → Finalize após alguns minutos"
echo "   → Sincronize com o app"
echo "   → Os dados aparecerão aqui automaticamente!"


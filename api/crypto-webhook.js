import { createClient } from '@supabase/supabase-js';

// Инициализация Supabase
const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

export default async function handler(req, res) {
    if (req.method === 'POST') {
        const { update_type, payload } = req.body;

        console.log("Получен вебхук тип:", update_type);

        // В Crypto Bot статус оплаты проверяется через update_type
        if (update_type === 'invoice_paid') {
            const userId = payload.payload; // Мы передавали ID юзера в поле payload при создании счета
            const sum = parseFloat(payload.amount);
            const asset = payload.asset;

            console.log(`Зачисление: ${sum} ${asset} для юзера ${userId}`);

            try {
                // 1. Получаем текущий баланс
                const { data: user, error: fetchError } = await supabase
                    .from('users')
                    .select('ton_balance')
                    .eq('user_id', userId)
                    .single();

                if (fetchError && fetchError.code !== 'PGRST116') {
                    throw fetchError;
                }

                // 2. Считаем новый баланс
                const currentBalance = user?.ton_balance || 0;
                const newBalance = currentBalance + sum;

                // 3. Обновляем базу
                const { error: updateError } = await supabase
                    .from('users')
                    .upsert({ 
                        user_id: userId, 
                        ton_balance: newBalance 
                    }, { onConflict: 'user_id' });

                if (updateError) throw updateError;

                console.log(`УСПЕХ! Юзер ${userId} пополнен. Баланс: ${newBalance}`);

            } catch (err) {
                console.error("Ошибка Supabase:", err.message);
            }
        }

        // Всегда отвечаем 200 для CryptoBot
        return res.status(200).send('OK');
    } else {
        return res.status(200).send('Webhook Active');
    }
}

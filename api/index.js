import { createClient } from '@supabase/supabase-js';

// Инициализация Supabase (берет данные из переменных Vercel автоматически)
const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(200).send('Webhook is active');
    }

    // ВНИМАНИЕ: CryptoBot присылает данные в объекте { update_type, payload }
    const { update_type, payload } = req.body;

    console.log("Получен вебхук тип:", update_type);

    if (update_type === 'invoice_paid') {
        // Вытаскиваем данные из вложенного объекта payload
        const userId = payload.payload; // Это ID юзера, который мы передали при создании счета
        const paidAmount = parseFloat(payload.amount);
        const asset = payload.asset;

        console.log(`Процесс зачисления: ${paidAmount} ${asset} для юзера ${userId}`);

        try {
            // 1. Получаем текущий баланс из Supabase
            const { data: user, error: fetchError } = await supabase
                .from('users')
                .select('ton_balance')
                .eq('user_id', userId)
                .single();

            if (fetchError && fetchError.code !== 'PGRST116') {
                console.error("Ошибка поиска юзера:", fetchError);
                throw fetchError;
            }

            // 2. Считаем новый баланс
            const currentBalance = user?.ton_balance || 0;
            const newBalance = currentBalance + paidAmount;

            // 3. Сохраняем (upsert)
            const { error: updateError } = await supabase
                .from('users')
                .upsert({ 
                    user_id: userId, 
                    ton_balance: newBalance 
                }, { onConflict: 'user_id' });

            if (updateError) {
                console.error("Ошибка обновления:", updateError);
                throw updateError;
            }

            console.log(`УСПЕХ! Баланс юзера ${userId} обновлен до ${newBalance}`);

        } catch (err) {
            console.error("Критическая ошибка:", err.message);
        }
    }

    // Обязательно отвечаем 200 OK, чтобы CryptoBot не слал повторы
    return res.status(200).send('OK');
}

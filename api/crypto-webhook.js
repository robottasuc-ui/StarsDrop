import { createClient } from '@supabase/supabase-js';

// Инициализация Supabase
const supabase = createClient(
    process.env.SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY
);

export default async function handler(req, res) {
    // CryptoBot отправляет POST запросы
    if (req.method === 'POST') {
        const { status, payload, amount, asset } = req.body;

        console.log("Получен вебхук:", req.body);

        if (status === 'paid') {
            const userId = payload; // ID пользователя из Telegram
            const sum = parseFloat(amount); // Сумма платежа

            console.log(`Процесс зачисления: ${sum} ${asset} для юзера ${userId}`);

            try {
                // 1. Пытаемся получить текущие данные юзера
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
                const newBalance = currentBalance + sum;

                // 3. Сохраняем обратно в Supabase (если юзера нет - создаст, если есть - обновит только TON)
                const { error: updateError } = await supabase
                    .from('users')
                    .upsert({ 
                        user_id: userId, 
                        ton_balance: newBalance 
                    }, { onConflict: 'user_id' });

                if (updateError) {
                    console.error("Ошибка при обновлении баланса:", updateError);
                    throw updateError;
                }

                console.log(`УСПЕХ! Баланс юзера ${userId} теперь: ${newBalance} TON`);

            } catch (err) {
                console.error("Критическая ошибка базы:", err.message);
                // Мы не выдаем 500 ошибку CryptoBot-у, чтобы он не слал повторы, 
                // но логируем её у себя в Vercel
            }
        }

        // ОТВЕТ ДЛЯ КРИПТОБОТА (Обязательно 200 OK)
        return res.status(200).send('OK');
    } else {
        return res.status(200).json({ message: "Webhook is active. Send POST request from CryptoBot." });
    }
}

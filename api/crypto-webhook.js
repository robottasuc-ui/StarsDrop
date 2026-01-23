export default async function handler(req, res) {
    // CryptoBot отправляет POST запросы
    if (req.method === 'POST') {
        const { status, payload, amount, asset } = req.body;

        console.log("Получен вебхук:", req.body);

        if (status === 'paid') {
            // payload — это ID пользователя, который мы передали при создании счета
            const userId = payload; 
            const sum = amount;

            console.log(`УРА! Пользователь ${userId} оплатил ${sum} ${asset}`);
            
            // Здесь будет логика зачисления в базу (пока просто подтверждаем получение)
        }

        // ОТВЕТ ДЛЯ КРИПТОБОТА (Обязательно 200 OK)
        return res.status(200).send('OK');
    } else {
        // Если кто-то зайдет по ссылке просто через браузер (GET)
        return res.status(200).json({ message: "Webhook is active. Send POST request from CryptoBot." });
    }
}

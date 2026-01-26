const axios = require('axios');

export default async function handler(req, res) {
    // Разрешаем запросы (CORS)
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    
    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    const { userId, chatId } = req.query;
    const BOT_TOKEN = process.env.BOT_TOKEN;

    if (!userId || !chatId) {
        return res.status(400).json({ subscribed: false, error: "Missing params" });
    }

    try {
        const url = `https://api.telegram.org/bot${BOT_TOKEN}/getChatMember?chat_id=${chatId}&user_id=${userId}`;
        const response = await axios.get(url);
        
        const status = response.data.result?.status;
        const isSubscribed = ['member', 'administrator', 'creator'].includes(status);

        return res.status(200).json({ subscribed: isSubscribed });
    } catch (error) {
        // Если юзер не найден или бот не в канале, вернется ошибка — считаем, что не подписан
        return res.status(200).json({ subscribed: false });
    }
}

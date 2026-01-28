import { kv } from '@vercel/kv';

export default async function handler(req, res) {
    // Разрешаем CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') return res.status(200).end();

    try {
        if (req.method === 'POST') {
            const { id, name, coins } = req.body;
            if (!id) return res.status(400).json({ error: "No ID" });

            // Сохраняем/обновляем данные пользователя в хеш-таблице "players"
            await kv.hset('players', { 
                [id]: JSON.stringify({ name, coins, lastUpdate: Date.now() }) 
            });

            return res.status(200).json({ success: true });
        }

        if (req.method === 'GET') {
            // Получаем всех игроков
            const allPlayers = await kv.hgetall('players');
            
            if (!allPlayers) return res.status(200).json([]);

            // Превращаем объект в массив и сортируем
            const leaderboard = Object.values(allPlayers)
                .map(item => typeof item === 'string' ? JSON.parse(item) : item)
                .sort((a, b) => b.coins - a.coins)
                .slice(0, 100);

            return res.status(200).json(leaderboard);
        }
    } catch (error) {
        console.error(error);
        return res.status(500).json({ error: error.message });
    }
}

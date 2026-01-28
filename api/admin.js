import { db } from '@vercel/postgres';

export default async function handler(req, res) {
    // 1. Подключаемся к базе
    const client = await db.connect();

    // МЕТОД GET: Отдаем список всех игроков
    if (req.method === 'GET') {
        try {
            const { rows } = await client.sql`SELECT * FROM users ORDER BY points DESC;`;
            return res.status(200).json(rows);
        } catch (error) {
            return res.status(500).json({ error: "Ошибка при получении списка" });
        }
    }

    // МЕТОД POST: Обновляем данные (баланс, герой и т.д.)
    if (req.method === 'POST') {
        const { user_id, points, active_hero_id, energy } = req.body;

        try {
            await client.sql`
                UPDATE users 
                SET points = ${points}, 
                    active_hero_id = ${active_hero_id}, 
                    energy = ${energy}
                WHERE user_id = ${user_id};
            `;
            return res.status(200).json({ message: "Данные успешно обновлены!" });
        } catch (error) {
            return res.status(500).json({ error: "Не удалось обновить данные" });
        }
    }
}

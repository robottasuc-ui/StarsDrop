export default async function handler(req, res) {
  if (req.method === 'POST') {
    const { status, payload, amount } = req.body;

    // Если оплата прошла успешно
    if (status === 'paid') {
      const userId = payload; // Это ID пользователя, который мы передали при создании счета
      console.log(`Пользователь ${userId} оплатил счет на сумму ${amount}`);
      
      // Здесь должен быть твой код для записи баланса в базу данных
    }

    // CryptoBot обязательно должен получить ответ 200 OK
    return res.status(200).send('OK');
  } else {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}

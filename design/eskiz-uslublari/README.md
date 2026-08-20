# Eskiz asosidagi dizayn — 3 uslub

Klientning qo'lda chizilgan eskizi bo'yicha qurilgan maketlar. Har uslubda
ikkita ekran: **bosh sahifa** va **kamera**.

Tuzilish hamma joyda bir xil (eskizdagidek):

**Bosh sahifa** — tepada `1700/2000`, markazda tana silueti, uning atrofida
to'rtta makro halqasi (chap-tepa, o'ng-tepa, o'ng-o'rta, chap-past), ostida
uchta qator (AI maslahati, eslatma, kunlik mashq), pastda uchta tugma
(uy, kamera, sozlama).

**Kamera** — o'ng tepada sozlama, katta vizir ramkasi, pastda galereya /
zatvor / qidiruv.

| Uslub | Fayl | Nima bilan farq qiladi |
|-------|------|------------------------|
| **A · Skeuomorphism** | `A1`, `A2` | Charm fon, metall kant, shisha qoplama, LED tablo. Har element hajmli: yuqoridan yorug'lik tushadi, pastda soya qoladi. Halqalar — fizik shkala, zatvor — konsentrik metall halqalar. |
| **B · Glassmorphism** | `B1`, `B2` | Rangli "mesh" fon ustida muzlatilgan shisha qatlamlari. Sirt yarim shaffof — orqadagi rang undan sizib turadi. Chuqurlik soya bilan emas, QATLAM bilan beriladi. |
| **C · Minimalizm (oq-qora)** | `C1`, `C2` | Rang yo'q, soya yo'q, to'ldirish yo'q. Faqat 1px kontur va bo'sh joy. Tugma "quti" emas — matn va ingichka chiziq. Ovqat ham kontur bilan chizilgan. |

## Ko'rish

```bash
cd design/eskiz-uslublari
npm install
npm start        # http://localhost:5199/A1-skeuo-home.html
```

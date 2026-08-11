# 🎨 RouletVoc Asset Guide & Replacement Directory

คู่มือการใส่และปรับแต่ง Asset รูปภาพและเสียงในเกม RouletVoc สามารถนำรูปภาพ `.png` (แนะนำ Transparent PNG ขนาด 512x512 หรือ 1024x1024) หรือไฟล์เสียง `.wav` มาวางทับในโฟลเดอร์เหล่านี้ได้ทันที!

---

## 📁 โครงสร้างโฟลเดอร์ Asset (Asset Categories)

```
assets/
├── items/           # 📦 รูปภาพการ์ดคำศัพท์ 12 หมวดห้องเรียน
├── gestures/        # 🖐️ รูปภาพไอคอนท่าทางภาษามือ
├── ui/              # 🎡 รูปภาพวงล้อรูเล็ตต์และเข็มชี้
├── audio/           # 🔊 ไฟล์เสียงอ่านคำศัพท์ภาษาอังกฤษ (WAV 115 wpm)
├── sounds/          # 🎵 ไฟล์เสียง Sound Effects ในเกม
└── custom/          # 🌟 โฟลเดอร์สำรองสำหรับใส่ Asset ปรับแต่งเพิ่มเติม
```

---

## 1. 📦 รายการรูปภาพคำศัพท์ (`assets/items/`)
| ไฟล์ | คำศัพท์ (EN) | ความหมาย (TH) | สถานะ Asset ปัจจุบัน | คำแนะนำในการปรับปรุง |
|---|---|---|---|---|
| `backpack.png` | Backpack | กระเป๋า | ✅ พร้อมใช้งาน | PNG ใส 512x512 |
| `book.png` | Book | หนังสือ | ✅ พร้อมใช้งาน | PNG ใส 512x512 |
| `chair.png` | Chair | เก้าอี้ | ✅ พร้อมใช้งาน | PNG ใส 512x512 |
| `clock.png` | Clock | นาฬิกา | ⚠️ Placeholder | สามารถเปลี่ยนรูปนาฬิกาสวยๆ มาทับได้ |
| `eraser.png` | Eraser | ยางลบ | ✅ พร้อมใช้งาน | PNG ใส 512x512 |
| `fan.png` | Fan | พัดลม | ⚠️ Placeholder | สามารถเปลี่ยนรูปพัดลมสวยๆ มาทับได้ |
| `notebook.png` | Notebook | สมุด | ⚠️ Placeholder | สามารถเปลี่ยนรูปสมุดเขียนมาทับได้ |
| `pen.png` | Pen | ปากกา | ✅ พร้อมใช้งาน | PNG ใส 512x512 |
| `pencil.png` | Pencil | ดินสอ | ✅ พร้อมใช้งาน | PNG ใส 512x512 |
| `ruler.png` | Ruler | ไม้บรรทัด | ✅ พร้อมใช้งาน | PNG ใส 512x512 |
| `table.png` | Table | โต๊ะ | ⚠️ Placeholder | สามารถเปลี่ยนรูปโต๊ะเรียนมาทับได้ |
| `window.png` | Window | หน้าต่าง | ⚠️ Placeholder | สามารถเปลี่ยนรูปหน้าต่างมาทับได้ |

---

## 2. 🖐️ รายการรูปภาพท่าทาง (`assets/gestures/`)
| ไฟล์ | ท่าทาง (Gesture) | การใช้งานในเกม |
|---|---|---|
| `gesture_pinch.png` | จีบนิ้ว (Pinch 🤏) | วงล้อหมุน & คำแนะนำเปิดการ์ด |
| `gesture_fist.png` | กำมือ (Fist ✊) | วงล้อหมุน & คำแนะนำเปิดการ์ด |
| `gesture_peace.png` | ชู 2 นิ้ว (Peace ✌️) | วงล้อหมุน & คำแนะนำเปิดการ์ด |
| `gesture_palm.png` | แบมือ (Open Palm 🖐️) | วงล้อหมุน & คำแนะนำเปิดการ์ด |
| `gesture_ok.png` | เครื่องหมาย OK (👌) | หน้ายืนยันความพร้อมก่อนเริ่มทีม |
| `gesture_point.png` | ชี้นิ้ว (Point ☝️) | ท่าทางเสริม |

---

## 3. 🎡 รายการ UI Components (`assets/ui/`)
| ไฟล์ | รายละเอียด |
|---|---|
| `roulette_wheel.png` | วงล้อรูเล็ตต์ 4 เซกเตอร์ (PNG 360x360) |
| `wheel_pointer.png` | เข็มชี้หมุนรูเล็ตต์ด้านบน (PNG 68x110) |

---

## 4. 🔊 รายการไฟล์เสียงอ่านคำศัพท์ (`assets/audio/`)
- `backpack.wav`
- `book.wav`
- `chair.wav`
- `clock.wav`
- `eraser.wav`
- `fan.wav`
- `notebook.wav`
- `pen.wav`
- `pencil.wav`
- `ruler.wav`
- `table.wav`
- `window.wav`

---

## 5. 🎵 รายการเสียง Effect (`assets/sounds/`)
- `tick.wav` - เสียงหมุนผ่านเซกเตอร์วงล้อ
- `wheel_win.wav` - เสียงวงล้อหยุดหมุน
- `countdown_beep.wav` - เสียงนับถอยหลัง 3.. 2.. 1..
- `countdown_go.wav` - เสียงเริ่มรอบเล่นเกม
- `lock.wav` - เสียงเล็งค้างการ์ดสำเร็จ
- `correct.wav` - เสียงตอบถูก / ออกเสียงถูกต้อง (+100 แต้ม)
- `wrong.wav` - เสียงตอบผิด / ออกเสียงไม่ตรง
- `ready_ping.wav` - เสียงเก็บชาร์จทำท่า OK
- `ok_ready.wav` - เสียงยืนยันพร้อมเริ่มทีม
- `podium_fanfare.wav` - เสียงเฉลิมฉลองหน้าสรุปผลอันดับ 1

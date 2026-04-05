# 06 — UI/UX Wireframes & Layout Descriptions

## Design System Snapshot

```
┌──────────────────────────────────────────────────────────────────┐
│ Hospital Dark Theme  │  --bg-base: #09111f (near black navy)     │
│                      │  --accent:  #3b82f6 (medical blue)        │
│                      │  --success: #22c55e (green reported)      │
│                      │  --warning: #f59e0b (yellow pending)     │
│                      │  Font: Inter 14px  │  Mono: JetBrains     │
└──────────────────────────────────────────────────────────────────┘
```

---

## Wireframe 1: Login Page

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   ┌──────────────────────────┐  ┌─────────────────────────┐    │
│   │   (Branding Panel)       │  │   (Form Panel)          │    │
│   │   bg: gradient dark navy │  │   bg: --bg-base         │    │
│   │                          │  │                         │    │
│   │        PACS++            │  │   Đăng nhập             │    │
│   │   [48px gradient text]   │  │   [subtitle text]       │    │
│   │                          │  │                         │    │
│   │   Hệ thống PACS Mini + RAG│  │  [label] Tên đăng nhập │    │
│   │   [22px heading]         │  │  [_____________ input]  │    │
│   │                          │  │                         │    │
│   │  Lưu trữ, quản lý và    │  │  [label] Mật khẩu       │    │
│   │  tìm kiếm thông minh... │  │  [_____________ input]  │    │
│   │   [14px body text]       │  │                         │    │
│   │                          │  │  [btn-primary full-width│    │
│   │  ── radial glow ──       │  │   Đăng nhập            ] │    │
│   │                          │  │                         │    │
│   │                          │  │  ──── divider ────      │    │
│   │                          │  │  admin / admin123       │    │
│   │                          │  │  dr.nam / doctor123     │    │
│   │                          │  │  [mono font, muted]     │    │
│   └──────────────────────────┘  └─────────────────────────┘    │
│              50%                           50%                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Wireframe 2: App Shell (AppLayout)

```
┌────────────────────────────────────────────────────────────────┐
│ SIDEBAR (240px)             │ MAIN AREA (flex-grow)            │
│ bg: #060f1c                 │                                  │
│ border-right: 1px #142035   │ ┌─────────────────────────────┐ │
│                             │ │ TOPBAR (60px)               │ │
│ ┌─────────────────────────┐ │ │ bg: #0a1625                 │ │
│ │ [P+] PACS++    [← btn] │ │ │ [Page Title]  [subtitle]    │ │
│ └─────────────────────────┘ │ │                  [actions]  │ │
│                             │ └─────────────────────────────┘ │
│ [CHỨC NĂNG label]           │                                  │
│ ● Worklist      ← active    │ ┌─────────────────────────────┐ │
│ ● Tìm kiếm                  │ │ PAGE CONTENT                │ │
│ ● Báo cáo                   │ │ padding: 24px               │ │
│                             │ │ overflow-y: auto            │ │
│ [QUẢN TRỊ label] ← admin    │ │                             │ │
│ ● Quản trị                  │ │  [Các components của page]  │ │
│                             │ │                             │ │
│ ─────────────────────────── │ │                             │ │
│ [AB] Nguyễn Văn A   [Thoát]│ │                             │ │
│      Bác sĩ                 │ │                             │ │
└─────────────────────────────┴─────────────────────────────────┘
```

**Sidebar Collapsed (64px):**
```
┌──────────┐
│[P+] [→]  │
│──────────│
│  ●       │  ← chỉ hiện dot, hover → tooltip bên phải
│  ●       │
│  ●       │
│──────────│
│  [AB]    │
└──────────┘
```

---

## Wireframe 3: Worklist Page

```
TOPBAR: [Worklist]  [44 ca chụp]
─────────────────────────────────────────────────────────────────

┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────┐
│ TỔNG CA CHỤP │ │ CHỜ ĐỌC      │ │ ĐÃ BÁO CÁO  │ │ XÁC NHẬN │
│     44       │ │     12       │ │     28       │ │    4     │
│ [blue top]   │ │ [yellow top] │ │ [green top]  │ │ [blue]   │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────┘

┌──── Upload DICOM (chỉ technician + admin) ─────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Kéo thả file .dcm vào đây  hoặc click để chọn file    │  │
│  │                (dashed border, hover → blue)             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘

┌──── Bộ lọc ─────────────────────────────────────────────────┐
│ [Ngày chụp input]  [Loại chụp select]  [Trạng thái select]  │
│                                      [Lọc btn] [Xoá btn]    │
└─────────────────────────────────────────────────────────────┘

┌─ table ────────────────────────────────────────────────────────┐
│ BỆNH NHÂN    │ NGÀY CHỤP │ LOẠI │ VỊ TRÍ │ TRẠNG THÁI │ ... │
├──────────────┼───────────┼──────┼────────┼────────────┼──────│
│ Nguyễn Văn A │ 2024-03-01│ [CT] │ CHEST  │ [●Chờ đọc] │[Xem]│
│ BN0001       │           │      │        │            │[Báo] │
├──────────────┼───────────┼──────┼────────┼────────────┼──────│
│ Trần Thị B   │ 2024-03-02│ [MR] │ HEAD   │[●Báo cáo] │[Xem] │
│ BN0002       │           │      │        │            │[Báo] │
└──────────────────────────────────────────────────────────────┘
  ↑ Click row → Viewer     ↑ mono font   ↑ colored badge
```

---

## Wireframe 4: Search Page

```
TOPBAR: [Tìm kiếm thông minh]  [RAG + NL2SQL]
─────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│ [Từ khoá] [Dense (BGE-M3)] [Hybrid ●active] [NL2SQL/Hỏi]   │
│ ─────────────────────────────────────────────────────────── │
│ [_____________________________________ input ][Tìm kiếm btn] │
│ Kết hợp Dense + BM25 + Keyword, tổng hợp bằng RRF.          │
└─────────────────────────────────────────────────────────────┘

── 5 kết quả ────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│ Nguyễn Văn A          2024-03-01      [CT]  [●Báo cáo]     │
│ Kết quả hình ảnh:                                           │
│ Hình ảnh tổn thương dạng đám mờ vùng đáy phổi phải...      │
│ Kết luận: Viêm phổi phân thuỳ                               │
│ Độ tương đồng: ████████░░ 82%                               │
└─────────────────────────────────────────────────────────────┘

── Tab NL2SQL ("bao nhiêu ca CT tháng 3?") ─────────────────────

┌─────────────────────────────────────────────────────────────┐
│ [STRUCTURED] [via rule_based]                               │
│ ◆ Có 12 ca chụp CT trong tháng 3/2024.                     │  ← answer box
│ SQL được sinh:                                              │
│ SELECT COUNT(*) FROM studies WHERE modality='CT'...         │  ← code block
│ ┌──────┬───────────┐                                        │
│ │ total│     12    │                                        │  ← sql results table
│ └──────┴───────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Wireframe 5: Report Page

```
TOPBAR: [Báo cáo chẩn đoán]         [Quay lại] [Xuất PDF] [Lưu]
─────────────────────────────────────────────────────────────────

┌──── Study Info (300px) ──┐ ┌──── Report Form ─────────────────┐
│ Thông tin ca chụp         │ │ Nội dung báo cáo    [●Đã báo cáo]│
│ ─────────────────────── │ │ ──────────────────────────────── │
│ BỆNH NHÂN                 │ │ Kết quả hình ảnh (Findings) *   │
│ Nguyễn Văn A             │ │ ┌─────────────────────────────┐ │
│ ─────────────────────── │ │ │ Hình ảnh tổn thương dạng    │ │
│ MÃ BN                     │ │ │ đám mờ vùng đáy phổi phải  │ │
│ BN0001                   │ │ │                             │ │
│ ─────────────────────── │ │ └─────────────────────────────┘ │
│ NGÀY CHỤP                 │ │                                  │
│ 2024-03-01               │ │ Kết luận (Conclusion) *          │
│ ─────────────────────── │ │ ┌─────────────────────────────┐ │
│ LOẠI                      │ │ │ Viêm phổi phân thuỳ phải    │ │
│ [CT]                     │ │ └─────────────────────────────┘ │
│ ─────────────────────── │ │                                  │
│ TRẠNG THÁI                │ │ Đề nghị xử trí                  │
│ [●Đã báo cáo]            │ │ ┌─────────────────────────────┐ │
│                           │ │ │ Điều trị kháng sinh...       │ │
│                           │ │ └─────────────────────────────┘ │
└───────────────────────────┘ └──────────────────────────────────┘
```

---

## Wireframe 6: Viewer Page

```
TOPBAR: [DICOM Viewer]  [Nguyễn Văn A]    [Worklist] [Báo cáo]
─────────────────────────────────────────────────────────────────

┌──── Info Panel (260px) ──┐ ┌──── Canvas Area (fill) ────────┐
│ THÔNG TIN CA CHỤP         │ │                                 │
│ ─────────────────────   │ │       [DICOM Image hoặc        │
│ Bệnh nhân  Nguyễn Văn A  │ │        Orthanc Web Viewer]     │
│ Mã BN      BN0001        │ │                                 │
│ Ngày chụp  2024-03-01    │ │    (bg: #000 thuần)            │
│ Loại       [CT]          │ │                                 │
│ Vị trí     CHEST         │ │                    ┌──────────┐ │
│ Trạng thái [●Chờ đọc]   │ │                    │ [Toolbar]│ │
│ Study UID  1.2.840...    │ │                    │ Phóng to │ │
│ ─────────────────────   │ │                    │ Thu nhỏ  │ │
│ ĐIỀU KHIỂN                │ │                    │ WW/WL    │ │
│ ┌────────┐ ┌────────┐   │ │                    └──────────┘ │
│ │Phóng to│ │Thu nhỏ│   │ │                                 │
│ └────────┘ └────────┘   │ │                                 │
│ ┌────────┐ ┌────────┐   │ │                                 │
│ │Di chuyển│ │Đặt lại│   │ │  Nếu không có DICOM:           │
│ └────────┘ └────────┘   │ │  "Ca chụp chưa có file DICOM   │
└───────────────────────────┘ │   trên Orthanc server."        │
                               └─────────────────────────────────┘
```

---

## Component States

### StatusBadge
```
● Chờ đọc    → bg: amber/10  | text: amber  | border: amber/20
● Đã báo cáo → bg: green/10  | text: green  | border: green/20
● Đã xác nhận→ bg: cyan/10   | text: cyan   | border: cyan/20
```

### ModalityBadge
```
[CT] [CR] [MR] [US] [DX]
→ bg: --bg-elevated | text: cyan | border: --border-light | font: mono
```

### Buttons
```
btn-primary   → bg: #3b82f6  hover: #2563eb
btn-secondary → bg: #132035  hover: #1a2d47  border: border-light
btn-ghost     → transparent  hover: bg-elevated
btn-danger    → bg: red/10   hover: bg: red    (full)
btn-sm        → height: 28px  btn-lg → height: 44px
```

### ScoreBar (Search results)
```
Độ tương đồng: [████████░░░░] 68%
               ← accent gradient fill on grey track
```

// ==========================================
// 1. CLASS CHA (Khuôn đúc gốc)
// ==========================================
class ClothingItem {
    // [ĐÓNG GÓI] private: Kín tuyệt đối. Chỉ class này mới được chạm vào.
    // Dù là class Con (Shirt) hay người ngoài (Main) đều KHÔNG thể sửa trực tiếp.
    private String name;
    private double price;

    // [KẾ THỪA] protected: Bí kíp gia truyền.
    // Người ngoài (Main) không được gọi, nhưng class Con (Shirt) thì lấy xài vô tư.
    protected String brand = "ETHEREAL";

    // [KHỞI TẠO] Constructor: Bắt buộc phải có Tên và Giá khi tạo sản phẩm
    public ClothingItem(String name, double price) {
        this.name = name;
        this.setPrice(price); // Gọi hàm setter để kiểm duyệt giá ngay từ lúc khởi tạo
    }

    // [GIAO TIẾP] public (Getter): Mở cửa cho người ngoài XEM tên
    public String getName() {
        return this.name;
    }

    // [GIAO TIẾP] public (Getter): Mở cửa cho người ngoài XEM giá
    public double getPrice() {
        return this.price;
    }

    // [GIAO TIẾP] public (Setter): Mở cửa cho người ngoài SỬA giá, NHƯNG BỊ KIỂM DUYỆT
    public void setPrice(double newPrice) {
        if (newPrice >= 0) {
            this.price = newPrice;
        } else {
            System.out.println("[CẢNH BÁO TỪ HỆ THỐNG] Lỗi: Không thể đặt giá âm cho sản phẩm!");
        }
    }
}

// ==========================================
// 2. CLASS CON (Kế thừa từ Cha)
// ==========================================
class Shirt extends ClothingItem {
    private String size;

    // Constructor của Class Con
    public Shirt(String name, double price, String size) {
        // TỪ KHÓA super(): Đẩy 'name' và 'price' lên cho Constructor của Cha xử lý
        super(name, price);
        this.size = size;
    }

    // Hàm public để in thông tin
    public void displayInfo() {
        System.out.println("\n--- THÔNG TIN SẢN PHẨM ---");
        // Chú ý: brand xài trực tiếp được vì nó là 'protected'
        // name và price phải gọi hàm get...() vì nó bị Cha khóa 'private'
        System.out.println("Thương hiệu: " + this.brand);
        System.out.println("Tên áo: " + this.getName());
        System.out.println("Size: " + this.size);
        System.out.println("Giá bán: $" + this.getPrice());
    }
}

// ==========================================
// 3. NƠI THỰC THI (Đóng vai trò là "Người ngoài")
// ==========================================
public class Main {
    public static void main(String[] args) {

        // 1. CHẠY CONSTRUCTOR: Ép buộc tạo đối tượng trọn vẹn ngay từ đầu
        Shirt aoThun = new Shirt("Áo Thun Basic", 25.0, "XL");
        aoThun.displayInfo();

        // 2. NGƯỜI NGOÀI CỐ TÌNH PHÁ HOẠI (Sẽ bị lỗi nếu bỏ dấu //)
        // aoThun.price = -100;    --> BÁO LỖI: Vì price là private (Giấu kín)
        // aoThun.brand = "Hàng Chợ"; --> BÁO LỖI: Vì brand là protected (Chỉ dành cho nội bộ)

        // 3. NGƯỜI NGOÀI TƯƠNG TÁC ĐÚNG LUẬT
        System.out.println("\n--- Thử hack giá âm thông qua hàm ---");
        aoThun.setPrice(-50); // Bị chặn lại bởi logic if-else trong Setter

        System.out.println("\n--- Đổi giá hợp lệ ---");
        aoThun.setPrice(30.0); // Chạy trót lọt vì giá trị > 0

        // Xem lại thông tin sau khi đổi giá
        aoThun.displayInfo();
    }
}
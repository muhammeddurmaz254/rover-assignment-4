import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math

class GoToGoalNode(Node):
    def __init__(self):
        super().__init__('go_to_goal_node')
        
        # Ödev şartı: Başlangıç noktası ile aynı doğrultuda olmayan bir hedef
        self.goal_x = 1.6
        self.goal_y = 0.5
        self.distance_tolerance = 0.1 # Hedefe ne kadar yaklaşınca duracağı (metre)
        
        # Hız komutları için Publisher ve konum okumak için Subscriber
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscriber_ = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        
        # Kontrol döngüsü
        self.timer_ = self.create_timer(0.1, self.move_to_goal)
        
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.goal_reached = False

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        
        # Quaternion'dan Euler açısına (yaw - Z eksenindeki dönüş) çevirme işlemi
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

    def move_to_goal(self):
        if self.goal_reached:
            return

        msg = Twist()
        
        # Öklid uzaklığı ile hedefe olan mesafe hesaplaması
        distance = math.sqrt((self.goal_x - self.current_x)**2 + (self.goal_y - self.current_y)**2)
        
        if distance >= self.distance_tolerance:
            # Hedefe yönelme açısını hesapla
            angle_to_goal = math.atan2(self.goal_y - self.current_y, self.goal_x - self.current_x)
            
            # Açısal hata (-pi ile pi arasına normalize edilir)
            angle_error = angle_to_goal - self.current_yaw
            while angle_error > math.pi:
                angle_error -= 2.0 * math.pi
            while angle_error < -math.pi:
                angle_error += 2.0 * math.pi
            
            # CPU render için çok daha düşük hız katsayıları
            msg.linear.x = 0.1 * distance
            
            # Maksimum hızı çok düşük bir limite (0.05 m/s) çekiyoruz
            if msg.linear.x > 0.05:
                msg.linear.x = 0.05
                
            # Dönüş hızı yarı yarıya yavaşlatıldı
            msg.angular.z = 0.5 * angle_error
            
            # Robot hedefe çok ters bir açıda bakıyorsa, önce dönmesi için ileri gitmesini durdur
            if abs(angle_error) > 0.5:
                msg.linear.x = 0.0
            
            self.publisher_.publish(msg)
            self.get_logger().info(f'Hedefe gidiliyor... Mesafe: {distance:.2f} m')
            
        else:
            # Noktaya varıldığında hızın sıfır olması
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            self.publisher_.publish(msg)
            self.get_logger().info('Hedefe ulaşıldı! Hız sıfırlandı.')
            self.goal_reached = True

def main(args=None):
    rclpy.init(args=args)
    node = GoToGoalNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
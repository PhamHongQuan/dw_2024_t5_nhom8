import io
import os
import time
import sys
import requests  # Thêm thư viện requests
import xml.etree.ElementTree as ET  # Thêm thư viện XML
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from selenium import webdriver
import pyperclip  # Thư viện hỗ trợ copy/paste
from datetime import datetime

# Đảm bảo rằng đầu ra được mã hóa theo UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Nhận ngày từ đối số
if len(sys.argv) < 2:
    print("Ngày không được truyền vào.")
    sys.exit(1)

input_date = sys.argv[1]  # Ngày được truyền từ Java

# Thiết lập ChromeDriver
chrome_options = Options()
chrome_options.headless = False  # Để dễ kiểm tra (True nếu không cần hiển thị trình duyệt)

# Khởi tạo trình duyệt
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

url = "https://vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia"
driver.get(url)
driver.execute_script("window.scrollBy(0, 300);")
time.sleep(2)

# Lấy ô chọn ngày và sao chép giá trị vào clipboard
date_picker = driver.find_element(By.ID, "datePicker")
pyperclip.copy(input_date)  # Sao chép ngày vào clipboard

# Dùng ActionChains để chọn trường và dán ngày vào
action = ActionChains(driver)
action.move_to_element(date_picker).click().perform()  # Click vào trường chọn ngày
time.sleep(1)  # Đảm bảo ô đã được focus
action.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()  # Chọn tất cả
action.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()  # Dán giá trị từ clipboard

# Đợi vài giây để trang web cập nhật
time.sleep(5)

# Cuộn trang xuống để làm nút "Xem thêm" hiển thị
driver.execute_script("window.scrollBy(0, 500);")  # Cuộn xuống 300px (bạn có thể điều chỉnh giá trị này nếu cần)
time.sleep(2)  # Đợi một chút để trang web tải thêm dữ liệu

# Tìm và nhấn vào nút "Xem thêm" nếu có
try:
    load_more_button = driver.find_element(By.ID, "load-more-label")
    load_more_button.click()
    time.sleep(3)  # Đợi vài giây để tải thêm dữ liệu
except Exception as e:
    print(f"Không tìm thấy nút 'Xem thêm'. Lỗi: {e}")

# Trích xuất dữ liệu tỷ giá từ trang web
exchange_rates = driver.find_elements(By.CSS_SELECTOR, "table.table-responsive tbody tr")
data = []
for rate in exchange_rates:
    cols = rate.find_elements(By.TAG_NAME, "td")
    if len(cols) == 5:
        currency_code = cols[0].text.strip()
        currency_name = cols[1].text.strip()
        buy = cols[2].text.strip()
        transfer = cols[3].text.strip()
        sell = cols[4].text.strip()
        data.append({
            "Currency Code": currency_code,
            "Currency Name": currency_name,
            "Buy": buy,
            "Transfer": transfer,
            "Sell": sell,
            "Date": input_date
        })

# Chuyển dữ liệu thành DataFrame
df = pd.DataFrame(data)

# Chuyển định dạng ngày sang yyyyMMdd
formatted_date = f"{input_date[6:]}{input_date[3:5]}{input_date[:2]}"  # Đổi lại thành yyyyMMdd

# Đảm bảo thư mục tồn tại
folder_selected = "D:\\DW_2024_T5_Nhom8\\file\\crawl\\vcb"
if not os.path.exists(folder_selected):
    os.makedirs(folder_selected)

# Lưu dữ liệu vào file CSV
excel_filename = f"{folder_selected}/vietcombank_data_{formatted_date}.csv"

# Lưu DataFrame ra file CSV với mã hóa UTF-8
df.to_csv(excel_filename, index=False, encoding="utf-8-sig")

# Đóng trình duyệt
driver.quit()

# Tải dữ liệu XML nếu cần
try:
    xml_url = "YOUR_XML_URL_HERE"  # Thêm URL của nguồn XML ở đây
    response = requests.get(xml_url)
    if response.status_code == 200:
        # Parse XML data
        root = ET.fromstring(response.content)

        # Lấy giá trị từ các phần tử XML
        date_time = root.find(".//DateTime").text
        source = root.find(".//Source").text

        # Tạo DataFrame từ dữ liệu XML
        xml_data = []
        for exrate_elem in root.findall(".//Exrate"):
            currency_code = exrate_elem.get("CurrencyCode")
            currency_name = exrate_elem.get("CurrencyName")
            buy = exrate_elem.get("Buy")
            transfer = exrate_elem.get("Transfer")
            sell = exrate_elem.get("Sell")

            # Thêm thông tin về ngân hàng và ngày vào dữ liệu
            xml_data.append({
                "Currency Code": currency_code,
                "Currency Name": currency_name,
                "Buy": buy,
                "Transfer": transfer,
                "Sell": sell,
                "BankName": "VCB",  # Thêm cột "BankName" và gán giá trị từ phần tử "Source" của XML
                "Date": datetime.now().strftime("%d/%m/%Y")  # Thêm cột "Date" và gán giá trị từ phần tử "DateTime" của XML
            })

        df_xml = pd.DataFrame(xml_data)

        # Lưu XML Data vào file CSV
        xml_excel_filename = f"{folder_selected}/vietcombank_xml_data_{datetime.now().strftime('%Y%m%d')}.csv"
        df_xml.to_csv(xml_excel_filename, index=False, encoding="utf-8-sig")

        print("XML Data saved to", xml_excel_filename)
    else:
        print("Failed to retrieve XML data. Status code:", response.status_code)
except Exception as e:
    print("An error occurred while retrieving or processing the XML data:", e)

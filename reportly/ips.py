from statistics import median

class IPS:
    
    def __init__(self, ips_dict):
        self.ips_dict = ips_dict
        self.median_out_ips = []
    
    def analyze_ips(self):
        ips_dict = self.ips_dict
        ips_count = len(ips_dict.keys())
        sigin_list = []
        ips_login_count = 0
        for ip in ips_dict:
            data = ips_dict[ip]
            ips_login_count = ips_login_count + data["count"]
            sigin_list.append(data["count"])
        
        #sorted_list = sorted(sigin_list)
        #median_loc = int(len(sigin_list) / 2)
        #median_val = sorted_list[median_loc]

        for ip in ips_dict:
            #data = ips_dict[ip]
            self.median_out_ips.append(ip)
            #if data["count"] < median_val:
                #div_val = abs(data["count"] - median_val)/median_val
                #if div_val*100 >= 100:
            #        self.median_out_ips.append(ip)

    def return_sus_ips(self):
        return self.median_out_ips

    def return_ip_info(self, ip):
        if self.ips_dict.get(ip) != None:
            return self.ips_dict[ip]


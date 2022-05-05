#!/usr/bin/python3
#by RandomGuy90 A.D.2021

from PIL import Image, ImageDraw, ImageFont
import random, time, sys, json

from queue import Queue
import _thread

from censorship.censorship import Censorship
from database.db_connector import Db_connector

from config import conf

from discord.notifications import Notify

class Make_img(Censorship, Db_connector):
	def __init__(self, q_list=None):
		super().__init__(q_list=q_list)

		

		print("init")

		self.FIRST_POST = None
		self.HOURS_PASSED = 0
		self.ALERT_SEND = False
		self.WARNING_SEND = False
		self.censor_flag = False
		

		if q_list:
			self.q_list = q_list
			self.load_from_threads()

	def gen(self) -> None:
		"generate image"
		xd = conf
		conf['logger'].info(f"generating new image")

	
		self.prepare_text()

		try:
			self.get_fonts()
		except:
			Notify(q_list=self.q_list, error="FONT_NOT_FOUfND")
			conf['logger'].error(f"font not found")

			sys.exit(1)

		self.get_size_txt()
		self.set_margins()
	
		# img = Image.new('RGB', (conf['width'], conf['height']), self.hex_to_rgb(conf['colorBackground']))
		self.get_bg_color()
		self.img_object = Image.new('RGB', (conf['width'], conf['height']), self.hex_to_rgb(self.bg_color))
		print((conf['width'], conf['height']))
		d = ImageDraw.Draw(self.img_object)

		#text 
		coords =(conf['margin']["left"] ,conf['margin']["top"])
		print(coords)
		d.text(coords, self.TEXT, fill=self.hex_to_rgb(conf['colorText']), font=self.font)
		d.rectangle((0, 0, conf['width']-conf['outline_thickness'], conf['height']-conf['outline_thickness']),width= conf['outline_thickness'], fill=None, outline=self.hex_to_rgb(conf['colorOutline']))

		#header
		self.create_header()

		#footer
		self.create_footer()

		img = Image.open(conf['image_path'], "r")
		img = img.resize(conf['image_size'], Image.ANTIALIAS)
		img = img.convert("RGBA")

		coords = (int(conf['insta_res'][1]*conf['logo_X_ratio']), int(conf['insta_res'][0]*conf['logo_Y_ratio']))

		self.img_object.paste(img, coords, img)

		#resizing and prepare to save
		img = img.convert("RGB")
		
		self.save_img()
		self.save_tumbnail()
		self.db_add_img()
	

		insta = self.q_list.get("2insta")  if self.q_list else None
		print(self.TEXT)
		self.req = {
			"filename": f"{conf['out_image_name']}.{conf['extension']}",
			"title": self.TEXT,
			"send": False
		}

		if conf['AUTORUN'] and not self.censor_flag:
			self.req["send"] = True

			if insta: insta.put(self.req)
			conf['logger'].info(f"image send automatically, {self.req['filename']}")
			self.SENT = True

		print("edit_ratio")
		self.edit_ratio()
	

	def save_img(self):
		self.img_object = self.img_object.resize(conf['insta_res'], Image.ANTIALIAS)
		self.filename = f"{conf['out_image_path']}/{conf['out_image_name']}.{conf['extension']}"
		try:
			self.img_object.save(self.filename)
		except FileNotFoundError:
			Notify(q_list=self.q_list,error="CANT_SAVE_IMG")
			conf['logger'].error(f" couldn't save image, {self.filename}")

			try:
				self.filename = f"{conf['out_image_path_BACKUP']}/{conf['out_image_name']}.{conf['extension']}"

				self.img_object.save(self.filename)
			except FileNotFoundError:
				Notify(q_list=self.q_list,error="CANT_SAVE_IMG_BACK")
				conf['logger'].critical(f" couldn't save image in backup location, {self.filename}")

				sys.exit(1)




	def save_tumbnail(self):
		self.img_object = self.img_object.resize(conf['thumb_res'], Image.ANTIALIAS)
		self.img_object.save(f"{conf['thumb_path']}/{conf['out_image_name']}_thumbnail.{conf['extension']}")
		
	def get_bg_color(self):
		if isinstance(conf['colorBackground'], list):
			x = random.randrange(0, len(conf['colorBackground'])-1)
			self.bg_color = conf['colorBackground'][x]
		else:
			self.bg_color = conf['colorBackground']

	def edit_ratio(self):
		# conf['POST_RATIO'] += 1
		conf['POST_COUNT'] += 1

		if self.FIRST_POST == None:
			self.FIRST_POST = int(time.time())

		self.HOURS_PASSED = int(time.time()) 
		self.HOURS_PASSED = ( self.HOURS_PASSED - self.FIRST_POST )/ 3600

		# if self.HOURS_PASSED:
		if self.HOURS_PASSED > 1:
			conf['POST_RATIO'] = int(conf['POST_COUNT'] / self.HOURS_PASSED)
		else:
			conf['POST_RATIO'] = int(conf['POST_COUNT'] / 1)

		print(conf['POST_RATIO'])

		
		if conf['POST_RATIO'] >= conf['POST_RATIO_ALERT']:
			conf['logger'].warning(f" post ratio alert, autorun off, {conf['POST_RATIO']}")

			print('-------------  TO MAY POSTS, AUTO RUN OFF')
			self.db_set_approved(state=None)
			# self.set_autorun(False)
			conf['AUTORUN'] = False
			# self.get_autorun()

			if self.ALERT_SEND == False:
				# d.put(self.req)
				Notify(q_list=self.q_list,error="POST_RATIO_ALERT", img=self.req.get("filename"))
				self.ALERT_SEND = True


		elif conf['POST_RATIO'] >= conf['POST_RATIO_WARNING']:
			print("POSTS ALERT ALERTTTT!!!!")
			conf['logger'].warning(f" post ratio warning, {conf['POST_RATIO']}")		

			if self. WARNING_SEND == False:
				# d.put(self.req)
				Notify(q_list=self.q_list ,error="POST_RATIO_WARNING", img=self.req.get("filename"))
				self.WARNING_SEND = True
		
		if conf['POST_RATIO'] < conf['POST_RATIO_WARNING']:
			conf['AUTORUN'] = True
			# self.set_autorun(True)




		# if (self.FIRST_POST - time.time()) > 3600000:
		# 	self.HOURS_PASSED +=1


	def get_size_txt(self)-> None:
		"get size of text object"

		testImg = Image.new('RGB', (1, 1))
		testDraw = ImageDraw.Draw(testImg)
		width, height = testDraw.textsize(self.TEXT, self.font)
		self.heightTXT = height
		self.widthTXT = width
		
		# conf['width'] = height if height > width else width
		# conf['height'] = width if width > height else height

		conf['width'] = conf['insta_res'][0]
		conf['height'] = conf['insta_res'][1]

	def hex_to_rgb(self, value) -> tuple:
		"convert hex value to rgb"

		value = value.lstrip('#')
		lv = len(value)
		return tuple(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))

	def get_fonts(self) -> None:
		"import fonts"
		
		self.font = ImageFont.truetype(conf['fontname'], conf['fontsize'])
		self.font_footer = ImageFont.truetype(conf['font_footer_name'], conf['font_footer_size'])
		self.font_header = ImageFont.truetype(conf['font_header_name'], conf['header_font_size'])

	def set_margins(self) -> None:
		"margins"
		
		conf['margin']["top"] = (conf['height'] - self.heightTXT) / 2 
		conf['margin']["left"] = (conf['width'] * 5) / 100
		conf['width'] = int(conf['width']+(conf['margin']["left"]*2))
	
	def create_footer(self) -> None:
		"creating image's footer"

		ftr = ImageDraw.Draw(self.img_object)
		footer_coords = (conf['margin']["left"], conf['insta_res'][1]*conf['footer_position_ratio'])
		# print(footer_coords)
		ftr.text(footer_coords, conf['TEXT_footer'], fill=self.hex_to_rgb(conf['colorText']), font=self.font_footer)

	def create_header(self) -> None:
		"creating footer with posting date"
		self.create_data()
		header = ImageDraw.Draw(self.img_object)
		header_coords = (conf['margin']["left"], conf['insta_res'][1]*conf['header_position_ratio'])
		# header.text(header_coords, conf['DATE'], fill=self.hex_to_rgb(conf['colorText']), font=conf['font_header'])
		header.text(header_coords, conf['DATE'], fill=self.hex_to_rgb(conf['colorText']), font=self.font_header)

		
	def create_data(self) -> None:
		"create data if not specified for header"
		if conf['DATE'] == None:
			date = time.localtime()
			yr = date.tm_year
			month  = str(date.tm_mon) if len(str(date.tm_mon)) == 2 else f"0{date.tm_mon}"
			day  = str(date.tm_mday) if len(str(date.tm_mday)) == 2 else f"0{date.tm_mday}"
			hour  = str(date.tm_hour) if len(str(date.tm_hour)) == 2 else f"0{date.tm_hour}"
			minutes  = str(date.tm_min) if len(str(date.tm_min)) == 2 else f"0{date.tm_min}"
			mil = int(round(time.time() * 1000))
			conf['DATE'] = f"{hour}:{minutes} {day}/{month}/{yr}"



	def prepare_text(self) -> str:
		"cut text and prepare to show"

		txt = self.TEXT.rsplit(" ")
		res_txt = ""
		words = conf['word_break']
		i = 0 
		for elem in txt:
			i+=1
			# res_txt.append(elem)
			res_txt = res_txt +" "+ elem
			#print(res_txt)
			if not i%words:
				res_txt = res_txt + "\n"

		self.TEXT = str(res_txt)	


		if self.censor_flag == True:
			self.censure_txt()

	def load_from_threads(self):

		while 1:
			self.SENT = False
			gen = self.q_list.get("2gen")
			insta = self.q_list.get("2insta")
			# q2 = self.q_list.get("2flask")
			# q2 = self.q_list.get("2tello")
			res = gen.get() 

			
			#res =  q2.get()

			data = res["text"]
			conf['out_image_name'] = res["title"]
			t = res["title"]
			self.censor_flag = res["censure_flag"]

			#2021 10 22 11 03 53
			conf['DATE'] = f"{t[8]}{t[9]}:{t[10]}{t[11]} {t[6]}{t[7]}/{t[4]}{t[5]}/{t[0:4]}"

			self.TEXT_tmp = data
			if data:
				self.TEXT = data
		
				self.gen()
			if res.get("send") and not self.SENT:
				res = {
				"title": conf['out_image_name'],
				"filename": f"{conf['out_image_name']}.{conf['extension']}"
				}

	

				insta.put(res)
				 
			else:
				pass
			


			time.sleep(0.01)
			



if __name__ == '__main__':

	asd = Make_img()
	asd.TEXT = "LOREM IPSUM ąśðæżćź„"
	asd.gen()
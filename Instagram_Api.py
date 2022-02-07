from instagrapi import Client
from notifications import Notify

from config import Config


class Instagram_api(Config):
    bot = None
    q_list=None
    def __init__(self, q_list=None):
        super().__init__(child_class=__class__.__name__)
        if q_list != None:
            self.q_list = q_list


    def login(self):
        self.bot = Client()
        # self.bot.set_proxy("http://80.211.246.8:8080")
        # print("proxy set")
        if self.LOGIN_INSTAGRAM != "" and self.PASSWORD_INSTAGRAM != "":
            self.bot.login(self.LOGIN_INSTAGRAM, self.PASSWORD_INSTAGRAM)
            self.logger.info(f"instagram logged")

            print("bot logged")
            Notify(q_list=self.q_list, error="INSTAGRAM_LOGGED")
        else:
            Notify(q_list=self.q_list, error="INSTAGRAM_LOGIN_SKIPPED")
            print("bot login skipped")

        return self.bot

    def upload_post(self, img_path, caption=""):
        self.logger.info(f"post uploaded. {img_path}")

        self.bot.photo_upload(
            img_path, 
            caption=caption
        )

    def upload_album(self, imgs_paths, caption=""):
        self.logger.info(f"instagram album loaded, {imgs_paths}")

        self.bot.album_upload(
            imgs_paths,
            caption = caption
        )


if __name__  == "__main__":
    path = ""
    insta = Instagram_api()
    insta.login()
    insta.upload_post(img_path=path, caption="hello world 2")
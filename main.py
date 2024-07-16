import logging
import random
import os
import vk_api # type: ignore

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Данные для авторизации
TOKEN = 'vk1.a.u06Ji1a4PDAnXX14meDsSifIAsDg-uagajeK1ndWRrMBMC403Y7gb1JzqZFn0vSDMEkZ3_ptVrkbDbbhxJSMraprSIdwPpXil_sV-py7Aw5837Kx4Cw4-dfE1ujru86yaFWWcXdsHe4qUJBBGRyg1oWb13pzJPEwyY6y8a6xcIokLxU7EkGEr8sk31o9HcpnyAnkY3bFog2PpAVLY5nEUw'
GROUP_ID = '224106070'
USER_ID = "585000883"  # Идентификатор вашего пользователя для получения списка друзей

if not TOKEN or not GROUP_ID or not USER_ID:
    logging.error("Access token, group ID, or user ID is not set.")
    exit(1)


def get_active_followers(vk, group_id, count=5):
    try:
        # Получаем подписчиков группы
        followers = vk.groups.getMembers(group_id=group_id, fields='id')['items']
        random.shuffle(followers)  # Перемешиваем подписчиков для случайного выбора

        active_followers = []

        for follower in followers:
            user_id = follower['id']
            try:
                # Проверяем активность пользователя (лайки и комментарии)
                likes = vk.likes.getList(type='post', owner_id=user_id, count=1000)['count']
                comments = vk.wall.getComments(owner_id=user_id, count=1000)['count']
                if likes + comments > 0:
                    active_followers.append(user_id)
                    if len(active_followers) >= count:
                        break
            except vk_api.exceptions.ApiError as e:
                logging.warning(f"Failed to get likes or comments for user {user_id}: {e}")

        # Если в группе недостаточно активных пользователей, берём у ваших друзей
        if len(active_followers) < count:
            friends = vk.friends.get(user_id=USER_ID, count=1000)['items']
            random.shuffle(friends)  # Перемешиваем друзей для случайного выбора

            for friend_id in friends:
                if friend_id not in active_followers:
                    active_followers.append(friend_id)
                    if len(active_followers) >= count:
                        break

        return active_followers[:count]
    except vk_api.exceptions.ApiError as e:
        logging.error(f"Failed to get followers: {e}")
        return []


def get_photos_from_user_wall(vk, user_id, count=5):
    try:
        # Получаем записи со стены пользователя
        wall = vk.wall.get(owner_id=user_id, count=10)['items']
        photos = [item for item in wall if
                  'attachments' in item and any(att['type'] == 'photo' for att in item['attachments'])]

        random.shuffle(photos)  # Перемешиваем фотографии для случайного выбора
        return photos[:count]
    except vk_api.exceptions.ApiError as e:
        logging.warning(f"Failed to get photos from user {user_id}: {e}")
        return []


def main():
    try:
        vk_session = vk_api.VkApi(token=TOKEN)
        vk = vk_session.get_api()

        active_followers = get_active_followers(vk, GROUP_ID)

        # Собираем фотографии от подписчиков
        photos_to_repost = []
        for follower_id in active_followers:
            photos = get_photos_from_user_wall(vk, follower_id)
            photos_to_repost.extend(photos)

        # Выбираем случайные фотографии для репоста
        random.shuffle(photos_to_repost)
        selected_photos = photos_to_repost[:5]

        # Формируем текст для поста
        post_message = ("💛 Like Time | LT 💛\n"
                        "Лайкаем и комментируем, чтобы попасть в следующий пост!")

        # Создаём массив вложений для поста
        attachments = []
        for photo in selected_photos:
            photo_attachment = next(att for att in photo['attachments'] if att['type'] == 'photo')['photo']
            attachment_str = f"photo{photo_attachment['owner_id']}_{photo_attachment['id']}"
            attachments.append(attachment_str)

        # Опубликовываем пост на стене группы от имени сообщества
        vk.wall.post(owner_id=f'-{GROUP_ID}', from_group=1, message=post_message, attachments=','.join(attachments))
        logging.info("Posted photos on group wall.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()

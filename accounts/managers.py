from django.contrib.auth.models import BaseUserManager


# class UserManager(BaseUserManager):
#     def create_user(self, username, email, full_name, password):
#         if not username:
#             raise ValueError('Username is required!')
#         if not email:
#             raise ValueError('Email is required!')
#         if not full_name:
#             raise ValueError('full name is required!')

#         user = self.model(email=self.normalize_email(email), username=username, full_name=full_name)
#         user.set_password(password)
#         user.save(using=self.db)
#         return user

#     def create_superuser(self, username, email, full_name, password):
#         user = self.create_user(username, email, full_name, password)
#         user.is_admin = True
#         user.save(using=self.db)
#         return user



# class UserManager(BaseUserManager):
#     def create_user(self, username, email, full_name, password=None, is_admin=False, is_staff=False, is_active=True):
#         if not username:
#             raise ValueError('Username is required!')
#         if not email:
#             raise ValueError("User must have an email")
#         if not password:
#             raise ValueError("User must have a password")
#         if not full_name:
#             raise ValueError("User must have a full name")

#         user.username = username
#         user = self.model(
#             email=self.normalize_email(email)
#         )
#         user.full_name = full_name
#         user.set_password(password)  # change password to hash
#         user.admin = is_admin
#         user.staff = is_staff
#         user.active = is_active
#         user.save(using=self._db)
#         return user
        
#     def create_superuser(self, username, email, full_name, password=None, **extra_fields):
#         if not username:
#             raise ValueError('Username is required!')
#         if not email:
#             raise ValueError("User must have an email")
#         if not password:
#             raise ValueError("User must have a password")
#         if not full_name:
#             raise ValueError("User must have a full name")

#         user.username = username 
#         user = self.model(
#             email=self.normalize_email(email)
#         )
#         user.full_name = full_name
#         user.set_password(password)
#         user.admin = True
#         user.staff = True
#         user.active = True
#         user.save(using=self._db)
#         return user
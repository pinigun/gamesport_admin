import re
import hashlib
import phonenumbers
from pydantic import BaseModel, ConfigDict, field_validator
    

class LogInModel(BaseModel):
    class Login(BaseModel):
        type: str
        value: str

    login:      str
    password:   str
    
    
    @field_validator("login")
    def validate_login(cls, value: str):
        # Проверяем, является ли значение email
        if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", value):
            return cls.Login(type="email", value=value)

        # Проверяем, является ли значение валидным номером телефона
        try:
            parsed_number = phonenumbers.parse(value, None)  # None = автоопределение страны
            if phonenumbers.is_valid_number(parsed_number):
                return cls.Login(
                    type="phone_number",
                    value=f'+{parsed_number.country_code}{parsed_number.national_number}'
                )  
        except phonenumbers.NumberParseException:
            pass

        raise ValueError("Invalid login: must be a valid email or phone number")
    

    def get_filter_data(self) -> dict:
        return {
            self.login.type: self.login.value,
            "password": hashlib.md5(self.password.encode()).hexdigest()
        }

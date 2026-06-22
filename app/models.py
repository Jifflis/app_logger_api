from app import db
import enum
from datetime import datetime,timezone


class LogLevel(enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class TokenStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    
class Platform(enum.Enum):
    WEB = "web"
    IOS = "ios"
    ANDROID = "android"
    MACOS = "macos"
    WINDOWS = "windows"
    UNKNOWN = "unknown"   
     
class FieldType(enum.Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    EMAIL = "email"
    BOOLEAN = "boolean"    


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True, index=True)
    email = db.Column(db.String(100), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # One user → many projects
    projects = db.relationship("Project", back_populates="user", cascade="all, delete-orphan")

    # One user → many tokens
    tokens = db.relationship("Token", back_populates="user", cascade="all, delete-orphan")

class Project(db.Model):
    __tablename__ = "projects"

    project_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)

    user = db.relationship("User", back_populates="projects")

    # One project → many devices, logs, and tags
    devices = db.relationship("Device", back_populates="project", cascade="all, delete-orphan")
    logs = db.relationship("DeviceLog", back_populates="project", cascade="all, delete-orphan")
    tags = db.relationship("DeviceTag", back_populates="project", cascade="all, delete-orphan")
    tokens = db.relationship("Token", back_populates="project", cascade="all, delete-orphan")
    logTags =db.relationship("LogTag", back_populates="project", cascade="all, delete-orphan")
    custom_field_definitions = db.relationship("CustomFieldDefinition", back_populates="project", cascade="all, delete-orphan")
      
      # enforce unique project name per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='uq_user_project_name'),
    )


class CustomFieldDefinition(db.Model):
    __tablename__ = "custom_field_definitions"

    field_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    field_type = db.Column(db.Enum(FieldType), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    project = db.relationship("Project", back_populates="custom_field_definitions")
    custom_field_values = db.relationship("CustomFieldValue", back_populates="field_definition", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("project_id", "name", name="uq_project_field_name"),
    )


class CustomFieldValue(db.Model):
    __tablename__ = "custom_field_values"

    value_id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey("custom_field_definitions.field_id"), nullable=False, index=True)
    instance_id = db.Column(db.String(100), db.ForeignKey("devices.instance_id"), nullable=False, index=True)
    value = db.Column(db.String(255), index=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    field_definition = db.relationship("CustomFieldDefinition", back_populates="custom_field_values")
    device = db.relationship("Device", back_populates="custom_field_values")

    __table_args__ = (
        db.UniqueConstraint(
            "instance_id",
            "field_id",
            name="uq_device_field_value"
        ),
        db.Index(
            "ix_custom_field_values_field_id_value",
            "field_id",
            "value"
        ),
    )
     
class Device(db.Model):
    __tablename__ = "devices"

    instance_id = db.Column(db.String(100), primary_key=True)
    device_id = db.Column(db.String(100), nullable=True, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=False, index=True)
    name = db.Column(db.String(100), index=True)
    model = db.Column(db.String(100))
    platform = db.Column(db.Enum(Platform), nullable=False, index=True, default=Platform.UNKNOWN)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = db.Column(db.DateTime)
    country = db.Column(db.String(100), nullable=True, index=True)
    watch_date = db.Column(db.DateTime, nullable=True, index=True)
    app_version = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(100),nullable = True)


    project = db.relationship("Project", back_populates="devices")

    # One device → many logs and tags
    logs = db.relationship("DeviceLog", back_populates="device", cascade="all, delete-orphan")
    tags = db.relationship("DeviceTag", back_populates="device", cascade="all, delete-orphan")
    # One device → many device_sessions
    sessions = db.relationship("DeviceSession", back_populates="device", cascade="all, delete-orphan")
    custom_field_values = db.relationship("CustomFieldValue", back_populates="device", cascade="all, delete-orphan")
    push_tokens = db.relationship("PushToken", back_populates="device", cascade="all, delete-orphan")


class PushToken(db.Model):
    __tablename__ = "pushTokens"

    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.String(100), db.ForeignKey("devices.instance_id"), nullable=False, index=True)
    token = db.Column(db.String(512), nullable=False, index=True)
    platform = db.Column(db.Enum(Platform), nullable=False, index=True, default=Platform.UNKNOWN)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    device = db.relationship("Device", back_populates="push_tokens")

    __table_args__ = (
        db.UniqueConstraint("instance_id", "token", name="uq_device_push_token"),
    )


class Instance(db.Model):
    __tablename__ = "instances"

    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.String(100), nullable=False, index=True)

    __table_args__ = (
        db.UniqueConstraint("instance_id", name="uq_instances_instance_id"),
    )


class DeviceLog(db.Model):
    __tablename__ = "device_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=False, index=True)
    instance_id = db.Column(db.String(100), db.ForeignKey("devices.instance_id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    level = db.Column(db.Enum(LogLevel), nullable=False, index=True)
    log_tag_id = db.Column(db.Integer, db.ForeignKey("log_tags.id"), index=True, nullable=True)
    actual_log_time = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    project = db.relationship("Project", back_populates="logs")
    device = db.relationship("Device", back_populates="logs")
    log_tag = db.relationship("LogTag", back_populates="device_logs")

    __table_args__ = (
        db.Index("idx_project_instance_time", "project_id", "instance_id", "actual_log_time"),
    )


class DeviceTag(db.Model):
    __tablename__ = "device_tags"

    instance_id = db.Column(db.String(100), db.ForeignKey("devices.instance_id"), nullable=False)
    tag_name = db.Column(db.String(100), nullable=False)
    tag_value = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=False, index=True)

    device = db.relationship("Device", back_populates="tags")
    project = db.relationship("Project", back_populates="tags")

    __table_args__ = (
        db.PrimaryKeyConstraint("instance_id", "tag_name", "tag_value"),
        db.Index("idx_instance_tag", "instance_id", "tag_name"),
    )


class Token(db.Model):
    __tablename__ = "tokens"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), nullable=False, unique=True, index=True)
    status = db.Column(db.Enum(TokenStatus), nullable=False, default=TokenStatus.ACTIVE)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=False, index=True)
    
    user = db.relationship("User", back_populates="tokens")
    project = db.relationship("Project", back_populates="tokens")
    created_at = db.Column(db.DateTime,  default=lambda: datetime.now(timezone.utc), index=True)


class DeviceSession(db.Model):
    __tablename__ = "device_sessions"

    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.String(100), db.ForeignKey("devices.instance_id"), nullable=False, index=True)
    actual_log_time = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    device = db.relationship("Device", back_populates="sessions")

    __table_args__ = (
        db.Index("idx_instance_logtime", "instance_id", "actual_log_time"),
    )


class LogTag(db.Model):
    __tablename__ = "log_tags"

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.project_id"), nullable=False, index=True)

    __table_args__ = (
        db.UniqueConstraint("tag", "project_id", name="uq_tag_per_project"),
    )

    project = db.relationship("Project", back_populates="logTags")
    device_logs = db.relationship("DeviceLog", back_populates="log_tag")

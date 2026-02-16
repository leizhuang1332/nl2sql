from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import IntEnum


class PermissionLevel(IntEnum):
    """权限等级枚举"""
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3


@dataclass
class TablePermission:
    """表权限数据类"""
    table_name: str
    permission_level: PermissionLevel
    allowed_columns: Optional[Set[str]] = None


class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.table_permissions: Dict[str, TablePermission] = {}

    def set_table_permission(
        self,
        table_name: str,
        permission_level: PermissionLevel,
        allowed_columns: Optional[List[str]] = None
    ):
        """
        设置表权限
        
        Args:
            table_name: 表名
            permission_level: 权限等级
            allowed_columns: 允许访问的列列表
        """
        self.table_permissions[table_name] = TablePermission(
            table_name=table_name,
            permission_level=permission_level,
            allowed_columns=set(allowed_columns) if allowed_columns else None
        )

    def can_read_table(self, table_name: str) -> bool:
        """
        检查是否可读取表
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 是否可读取
        """
        perm = self.table_permissions.get(table_name)
        if not perm:
            return False
        return perm.permission_level >= PermissionLevel.READ

    def can_write_table(self, table_name: str) -> bool:
        """
        检查是否可写入表
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 是否可写入
        """
        perm = self.table_permissions.get(table_name)
        if not perm:
            return False
        return perm.permission_level >= PermissionLevel.WRITE

    def can_admin_table(self, table_name: str) -> bool:
        """
        检查是否可管理表
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 是否可管理
        """
        perm = self.table_permissions.get(table_name)
        if not perm:
            return False
        return perm.permission_level >= PermissionLevel.ADMIN

    def can_access_column(self, table_name: str, column: str) -> bool:
        """
        检查是否可访问列
        
        Args:
            table_name: 表名
            column: 列名
            
        Returns:
            bool: 是否可访问
        """
        perm = self.table_permissions.get(table_name)
        if not perm:
            return False
        if perm.allowed_columns is None:
            return True
        return column in perm.allowed_columns

    def get_table_permission(self, table_name: str) -> Optional[TablePermission]:
        """
        获取表权限
        
        Args:
            table_name: 表名
            
        Returns:
            Optional[TablePermission]: 表权限
        """
        return self.table_permissions.get(table_name)

    def get_allowed_columns(self, table_name: str) -> Optional[Set[str]]:
        """
        获取表允许访问的列
        
        Args:
            table_name: 表名
            
        Returns:
            Optional[Set[str]]: 允许访问的列集合
        """
        perm = self.table_permissions.get(table_name)
        if not perm:
            return None
        return perm.allowed_columns

    def load_from_config(self, config: Dict):
        """
        从配置加载权限
        
        Args:
            config: 配置字典
        """
        column_permissions = config.get("column_permissions", {})
        for table, perms in column_permissions.items():
            level_str = perms.get("level", "READ")
            try:
                level = PermissionLevel[level_str]
            except KeyError:
                level = PermissionLevel.READ
            columns = perms.get("columns")
            self.set_table_permission(table, level, columns)

    def clear(self):
        """清除所有权限"""
        self.table_permissions.clear()

    def get_all_tables(self) -> List[str]:
        """
        获取所有已配置权限的表
        
        Returns:
            List[str]: 表名列表
        """
        return list(self.table_permissions.keys())

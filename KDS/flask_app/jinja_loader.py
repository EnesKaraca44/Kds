"""Jinja sablon yukleyici: UTF-8 oncelikli, Windows ANSI (cp1254) yedekli."""

import os
import posixpath

from jinja2 import FileSystemLoader, TemplateNotFound
from jinja2.loaders import split_template_path
from jinja2.utils import open_if_exists


class ResilientFileSystemLoader(FileSystemLoader):
    """
    Sunucuda sablonlar bazen Notepad ile ANSI/cp1254 kaydediliyor.
    Flask varsayilan UTF-8 okumasi UnicodeDecodeError verir; bu loader dener.
    """

    def _decode_template_bytes(self, raw: bytes) -> str:
        """
        UTF-8 oncelikli. Tek bozuk byte yuzunden tum dosyayi cp1254 sanma;
        o durumda Turkce karakterler ? olur.
        """
        try:
            return raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            pass
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            pass
        try:
            text = raw.decode("cp1254")
            if text.count("?") <= 2:
                return text
        except UnicodeDecodeError:
            pass
        return raw.decode("utf-8", errors="replace")

    def get_source(self, environment, template):
        pieces = split_template_path(template)
        for searchpath in self.searchpath:
            filename = posixpath.join(searchpath, *pieces)
            f = open_if_exists(filename)
            if f is None:
                continue
            with f:
                raw = f.read()

            source = self._decode_template_bytes(raw)
            if source is None:
                continue

            mtime = os.path.getmtime(filename)

            def uptodate():
                try:
                    return os.path.getmtime(filename) == mtime
                except OSError:
                    return False

            return source, filename, uptodate

        raise TemplateNotFound(template)

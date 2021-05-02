class Resource:
    def __init__(self, resource=None, deleter=None):
        self.__resource = resource
        self.__deleter = deleter
        self.__ref_count = 0

    """
    Garbage collector is not reliable, but in case this resource is indeed garbage collected, we attempt to release any
    associated native resources, before allowing the GC to collect this object.
    """
    def __del__(self):
        self.__release()

    def __enter__(self):
        self.__ref()
        return self.__resource

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__unref()
        return False

    def __ref(self):
        self.__ref_count += 1
        return self

    def __unref(self):
        self.__ref_count -= 1
        if self.__ref_count <= 0:
            self.__release()
        return self

    def ref(self):
        self.__ref()
        return self

    def unref(self):
        self.__unref()
        return self

    def release(self):
        self.__release()
        return self

    def is_empty(self):
        return self.__resource is None

    def __release(self):
        self.__ref_count = 0
        if self.__resource is not None and callable(self.__deleter):
            self.__deleter(self.__resource)
            self.__resource = None

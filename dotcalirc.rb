# Sample rc file for cali
class Cali
  def preinit_hook
    @default_dates = "#{ENV['HOME']}/dates"
  end
  def postinit_hook
    define_key('.',:showevents)
  end
  def define_key(key,action)
    key = key[0] if key.instance_of? String
    @key[key]=action
  end
end

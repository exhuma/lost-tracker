Remote API
==========


Remote URLs which should be accepted. The codecs are currently stored in the
Android client::

    GET  /station/<station_name>/dashboard
      << DashboardCodec

    GET  /station/<station_name>
      << StationStateCodec

    PUT  /group_state/<group_name>/<station_name>
      >> GroupInfoCodec
      << GroupInfoCodec

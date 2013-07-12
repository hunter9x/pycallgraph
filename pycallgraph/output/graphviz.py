from pycallgraph.output import Output


class GraphvizOutput(Output):

    @classmethod
    def add_arguments(self, subparsers):
        subparser = subparsers.add_parser('graphviz-source',
            help='Graphviz source generation')

        subparser.add_argument('-o', '--output-file', type=str,
            default='pycallgraph.dot',
            help='The generated GraphViz dot source (pycallgraph.dot)')


    def done(self):
        defaults = []
        nodes = []
        edges = []

        # Define default attributes
        for comp, comp_attr in graph_attributes.items():
            attr = ', '.join('%s = "%s"' % (attr, val)
                             for attr, val in comp_attr.items() )
            defaults.append('\t%(comp)s [ %(attr)s ];\n' % locals())

        # Define nodes
        for func, hits in func_count.items():
            calls_frac, total_time_frac, total_time, total_memory_in_frac, \
                total_memory_in, total_memory_out_frac, total_memory_out = \
                _frac_calculation(func, hits)

            col = settings['node_colour'](calls_frac, total_time_frac)
            attribs = ['%s="%s"' % a for a in settings['node_attributes'].items()]
            node_str = '"%s" [%s];' % (func, ', '.join(attribs))
            if time_filter==None or time_filter.fraction <= total_time_frac:
                nodes.append( node_str % locals() )

        # define edges
        for fr_key, fr_val in call_dict.items():
            if not fr_key: continue
            for to_key, to_val in fr_val.items():
                calls_frac, total_time_frac, total_time, total_memory_in_frac, total_memory_in, \
                   total_memory_out_frac, total_memory_out = _frac_calculation(to_key, to_val)
                col = settings['edge_colour'](calls_frac, total_time_frac)
                edge = '[ color = "%s", label="%s" ]' % (col, to_val)
                if time_filter==None or time_filter.fraction < total_time_frac:
                    edges.append('"%s"->"%s" %s;' % (fr_key, to_key, edge))

        defaults = '\n\t'.join( defaults )
        nodes    = '\n\t'.join( nodes )
        edges    = '\n\t'.join( edges )

        dot_fmt = ("digraph G {\n"
                   "    %(defaults)s\n\n"
                   "    %(nodes)s\n\n"
                   "    %(edges)s\n}\n"
                  )
        return dot_fmt % locals()

    def make_dot_graph(fp, format='png', tool='dot'):
        '''Creates a graph using a Graphviz tool that supports the dot
        language. It will output into a file specified by filename with the
        format specified.  Setting stop to True will stop the current trace.
        '''
        if stop:
            stop_trace()

        dot_data = get_dot()

        # normalize filename
        regex_user_expand = re.compile('\A~')
        if regex_user_expand.match(filename):
            filename = os.path.expanduser(filename)
        else:
            filename = os.path.expandvars(filename)  # expand, just in case

        if format == 'dot':
            f = open(filename, 'w')
            f.write(dot_data)
            f.close()

        else:
            # create a temporary file to be used for the dot data
            fd, tempname = tempfile.mkstemp()
            with os.fdopen(fd, 'w') as f:
                f.write(dot_data)

            cmd = '%(tool)s -T%(format)s -o%(filename)s %(tempname)s' % locals()
            try:
                ret = os.system(cmd)
                if ret:
                    raise PyCallGraphException( \
                        'The command "%(cmd)s" failed with error ' \
                        'code %(ret)i.' % locals())
            finally:
                os.unlink(tempname)


class GraphvizImageOutput(GraphvizOutput):

    @classmethod
    def add_arguments(self, subparsers):
        subparser = subparsers.add_parser('graphviz-image',
            help='Graphviz image generation')

        subparser.add_argument('-o', '--output-file', type=str,
            default='pycallgraph.png',
            help='The generated GraphViz image (pycallgraph.png)')


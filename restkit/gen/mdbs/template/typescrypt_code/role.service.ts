import { _HttpClient } from '@core/services/http.client';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs/Observable';
import { ModleRole, QueryParam } from './model';
import { environment } from '../../environments/environment';
import 'rxjs/add/operator/catch';
const SERVER_URL = environment.SERVER_URL;


@Injectable()
export class RoleService {

    private BIZ_URL = '/roleData.json';

    constructor(private http: _HttpClient) {
    }

    parseQueryParam(queryParam: Array<QueryParam>): any {
        const where = {};
        for (const query of queryParam) {
            const qv = {};
            qv[query.op] = query.value;
            where[query.key] = qv;
        }
        return where;
    }

    get(queryParam: Array<QueryParam>, PageIndex = 1, pageSize = 10, sort = '') {
        // fix laster version
        const param = { 'page': [PageIndex, pageSize] };
        if (sort !== '') {
            param['sort'] = sort;
        }
        param['where'] = this.parseQueryParam(queryParam);

        return this.http.get(SERVER_URL + this.BIZ_URL, param);
    }

    put(role?: ModleRole) {
            ``
    }

    post(role?: ModleRole) {
        return this.http.post(SERVER_URL + this.BIZ_URL, role);
    }

    delete(roleId?: string) {
        const param = { 'roleId': roleId };
        return this.http.delete(SERVER_URL + this.BIZ_URL, param);
    }

}
